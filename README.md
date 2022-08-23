## Lattice Match for Organic Heteroepitaxy

### Dependencies
- `python>=3.6`
- `pip install pandas shapely`.
- `CSD-API`

### Retrieve data from CSD
- CSD (The Cambridge Structural Database) version 539, # of entries 961466.
- Crystal structures of organic molecules should satisfy the following:
  1. Only one kind of molecule (i.e. no co-crystals);
  2. There are at least two conjugated rings;
  3. Molecular weight > 300 and < 1000.
- 280480 such structures were found:
  1. The script for this task is `grep2csv.py`, `CSD-API` is required;
  2. Their lattice parameters were stored in `latdata.csv`.

### Calculate the fit parameter
- The fit parameter is defined in `SI: equation 1`.
  - Let `S` (substrate) and `T` (top layer) be the sets of points in two parallelograms defined 
  by triplets `(a, b, gamma)`,
  we define the fit parameter M as
      ```
      M = union(S-T, T-S).area/S.area
      ```
  - For `T` the triplet can also be `(a, c, beta)`(`010` plane) or 
  `(b, c, alpha)`(`100` plane), the smallest `M` is used.
  - Only aforementioned three low-index planes are considered.
- `python match.py` will read `latadata.csv` and generate `match_results.xlsx`.
- `match_results.xlsx` last column contains the calculated similarity

### Visualization
`CSD-API` has a funtion to write structure picture, in `SVG` or `PIL`
```python
from ccdc.diagram import DiagramGenerator
dg = DiagramGenerator()
dg.settings.return_type = 'SVG'  # save in html
img = dg.image(entry.molecule.components[0])
```
here img is already html string, it comes handy if combined with `pandas`:
```python
df = pd.DataFrame(results, columns=column_idx)  # results is a list of lists
htmlstring = df[['CSD id link', 'img']].to_html(escape=False, justify='center')
htmlstring = htmlstring.replace('\\n<svg', "<svg")  # somehow it writes an additional \n
htmlstring = htmlstring.replace('</svg>\\n', "</svg>")
with open('results.html', 'w') as f:
    f.write(htmlstring)
```
