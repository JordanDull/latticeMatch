import math
import pandas as pd
from shapely.geometry.polygon import Polygon
from ccdc.descriptors import CrystalDescriptors
from ccdc.io import EntryReader
from ccdc.io import EntryReader
from ccdc.io import MoleculeReader
import numpy as np

'''
read csv generated by grep2csv.py

for each entry, calculate value M based on a given triplet (a, b, gamma)

0 < asub < bsub, gammasub <= 90

let S and T (top layer) be the sets of points in two parallelograms defined by triplets (a, b, gamma), 
we define a similarity measure M as: M = union(S-T, T-S).area/S.area
'''


def cos(a):
    a = math.radians(a)
    return round(math.cos(a), 6)  # shapely interscetion does weird things if not rounded

def arccos(a):
    x =  round(math.acos(a), 6)
    x = math.degrees(x)
    return x


def sin(a):
    a = math.radians(a)
    return round(math.sin(a), 6)


def get_polygon(triplet):
    a, b, g = triplet
    if g > 90:
        g = 180 - g
    p = Polygon(
        [
            (0, 0),
            (b*cos(g), b*sin(g)),
            (a + b*cos(g), b*sin(g)),
            (a, 0)
        ]
    )
    return p


def cal_m_triplet(S, T):
    ps = get_polygon(S)
    pt = get_polygon(T)
    m1 = abs((ps.area + pt.area - 2*ps.intersection(pt).area)/ps.area)
    T[0], T[1] = T[1], T[0]
    pt = get_polygon(T)
    m2 = abs((ps.area + pt.area - 2*ps.intersection(pt).area)/ps.area)
    return min(m1, m2)

def cal_m_params(S, params):
    idcode, a, b, c, alpha, beta, gamma = params
    reader = EntryReader('csd')
    crystal = reader.crystal(idcode)
    try:
        morphology = CrystalDescriptors.Morphology(crystal)
    except:
        return
    
    if (a == 0 or b == 0 or c == 0 or alpha == 0 or beta == 0 or gamma == 0):
        return
    else:
        x1 = a*cos(gamma)
        y1 = math.sqrt((math.pow(a, 2)) - (math.pow(x1, 2)))
        x3 = c*cos(alpha)
        y3 = (a*c*cos(beta)-x1*x3)/y1
        z3 = math.sqrt((math.pow(c, 2)) - math.pow(x3, 2) - math.pow(y3, 2))
    
    
        # For (110) plane
        s1 = math.sqrt(math.pow((x1 - b), 2) + math.pow(y1, 2))
        a1 = arccos((x3*(x1 - b) + y3*y1)/(c*s1))
        #print(s1)
        #print(a1)
     
        # For (101) plane
        s2 = math.sqrt(math.pow((x1 - x3), 2) + math.pow(y1 - y3, 2) + 
                       math.pow((-z3), 2))
        a2 = arccos((x1 - x3)/s2)
        #print(s2)
        #print(a2)
        
        # For (011) plane
        s3 = math.sqrt(math.pow((b - x3), 2) + math.pow((y3), 2) + math.pow((z3), 2))
        a3 = arccos((x1*(b - x3)-y1*y3)/(a*s3))
        #print(s3)
        #print(a3)
        
        triplets = [[a, b, gamma], [a, c, beta], [b, c, alpha], [c, s1, a1],
                    [b, s2, a2], [a, s3, a3]]
        
        facets = morphology.facets
        
        all_miller_indices = [f.miller_indices for f in facets]
        
        
        rel_areas = [round(morphology.relative_area(mi), 3) for mi in all_miller_indices]

        min_plane = math.inf
        i = 0
        
        for t in triplets:
            i += 1
            x = cal_m_triplet(S, t)
            if min_plane > x:
                min_plane = x
                j = i
        if j == 1:
            j = '(001)' 
        elif j == 2:
            j = '(010)'
        elif j == 3:
            j = '(100)'
        elif j == 4:
            j = '(110)'
        elif j == 5:
            j = '(101)'
        elif j == 6:
            j = '(011)'
       
            
        i = 0
        match = False
        max_area = max(rel_areas)
       
        mil = all_miller_indices[0]
        
        for area in rel_areas:
            i += 1
            if area == max_area:
                mil = all_miller_indices[i-1]
                order = mil.order
                h = mil.hkl[0]
                k = mil.hkl[1]
                l = mil.hkl[2]
                lse_plane = "(" + str(h) + str(k) + str(l) + ")"
                if order > 1:
                    h = h // order
                    k = k // order
                    l = l // order
                hkl = "(" + str(h) + str(k) + str(l) + ")"
                match = (hkl == j)               
                        
        return min_plane, j, lse_plane, match
     

if __name__ == '__main__':

    #S = [7.175, 14.435, 90] # this is from rubrense
    #S = [11.34, 15.88, 87.68] # this is from NPB
    #S = [9, 19.580, 89.86] # this is from 4CZIPN (002)
    S = [19.313, 12.6864, 90] # this is from TPBi
    
    #S = [14.435, 27.908, 90] #for testing
    df = pd.read_csv('latdatashort.csv', sep=";;;", engine="python")
    allparams = df.values[:, 1:8]
    result = pd.Series([cal_m_params(S, params) for params in allparams], index=df.index)

    results = pd.DataFrame(result.values.tolist(), index = result.index, columns = ['m', 'plane', 'low energy plane', 'match?'])
    df = pd.merge(df, results, right_index=True, left_index=True)
    
    df_id = df.iloc[:,2]
    csd_mol_reader = MoleculeReader('CSD')

    mol = pd.Series([csd_mol_reader.molecule(df_id[i]) for i in range(len(df))])
    mol_smile = pd.Series([mol[i].smiles for i in range(len(mol))])
    mol_smiles = pd.DataFrame(mol_smile.values.tolist(), index = mol_smile.index, columns = ['Smile ID'])
    df = pd.merge(df, mol_smiles, right_index=True, left_index=True)
    
    print('matching against', S)
    df.to_excel('match_results.xlsx')
