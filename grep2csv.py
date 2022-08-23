from ccdc.io import EntryReader
import pandas as pd
import sys
'''
Crawl CSD to get cif files of crystal structures. Filter:
1. 1 kind of molecule
2. there are at least two conjugated rings
3. molecular weight >300 and <1000

write csdid, a, b, c, alpha, beta, gamma, Mw, Z into latdata.csv, this will be used by match.py
using ;;; as a delimiter
'''

pd.set_option('display.max_colwidth', -1)  # unset limit

csd_entry_reader = EntryReader('CSD')
# print(csd_version())  # 539
# print(len(csd_entry_reader))  # 961466


def is_one_kind_mol(entry):  #modified to include materials that have identical molecules in components
    if len(entry.molecule.components) == 1:
        return 1
    elif len(set(mol.smiles for mol in entry.molecule.components)) == 1:
        return 1
    else:
        return 0
    #if len(entry.molecule.components) == 1:
    #    return 1
    #else:
    #    return 0


def is_conjugated(entry):
    rings = entry.molecule.components[0].rings
    if len(rings) < 2:
        return 0
    nrings = 0
    for r in rings:
        if r.is_fully_conjugated:
            nrings += 1
        if nrings > 1:
            return 1
    return 0


def utfencode(s):
    #if isinstance(s, unicode):
     #   return s.encode('utf-8')
    return str(s)


def csdid2link(csdid):
    csdid = csdid.encode('utf-8')
    # e.g. https://www.ccdc.cam.ac.uk/structures/Search?Ccdcid=ABEBUF
    link = "<a href='http://www.ccdc.cam.ac.uk/structures/Search?Ccdcid=" + str(csdid) + "'>" + str(csdid) + "</a>"
    return link


def doi2link(doi):
    if doi is None:
        return doi
    return "<a href='https://doi.org/" + str(doi.encode('utf-8')) + "'>" + str(doi.encode('utf-8')) + "</a>"


def roundfloat(f):
    if isinstance(f, float):
        return round(f, 2)
    return f


def main():
    column_idx = ['csdid', 'a', 'b', 'c', 'alpha', 'beta', 'gamma', 'Mw', 'Z']
    rescsv = open('latdata.csv', 'a')
    rescsv.write(";;;" + ";;;".join(column_idx) + "\n")
    # main loop
    idxcounter = 0
    # for entry in [csd_entry_reader[i] for i in range(10)]:  # debug before launching
    numOfEntries=len(csd_entry_reader)
    entryNum=1
    for entry in csd_entry_reader:
        if entryNum%1000==0:
            print(entryNum,"/",numOfEntries)
        entryNum=entryNum+1
        # add filters
        if not is_one_kind_mol(entry):
            continue
        if not is_conjugated(entry):
            continue
        if not 1000 > entry.molecule.components[0].molecular_weight > 300:
            continue
        info = [
            entry.identifier,
            entry.crystal.cell_lengths[0],
            entry.crystal.cell_lengths[1],
            entry.crystal.cell_lengths[2],
            entry.crystal.cell_angles[0],
            entry.crystal.cell_angles[1],
            entry.crystal.cell_angles[2],
            entry.molecule.components[0].molecular_weight,
            entry.crystal.z_value,
        ]
        info = [roundfloat(j) for j in info]
        info = [utfencode(j) for j in info]
        rescsv.write(str(idxcounter) + ";;;" + ";;;".join(info) + "\n")
        idxcounter += 1
    rescsv.close()


def cleanup():
    sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        cleanup()
