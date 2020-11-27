
grid_field_3d_template = """EX Version: 2
Region: /
!#mesh mesh3d, dimension=3, face mesh=mesh2d, nodeset=nodes
Shape. Dimension=3, line*line*line
{0}
"""

temp = """EX Version: 2
Region: /
!#mesh mesh3d, dimension=3, face mesh=mesh2d, nodeset=nodes
Shape. Dimension=3, line*line*line
#Scale factor sets=0
#Nodes=0
#Fields=1
1) potential, field, real, #Components=1
 value. l.Lagrange*l.Lagrange*l.Lagrange, no modify, grid based.
 #xi1=2, #xi2=3, #xi3=2
Element: 1
 Values :
  0.000000000000000e+00  1.500000000000000e+00  3.000000000000000e+00
  3.233334000000000e+00  2.409252000000000e+00  3.440926000000000e+00
  6.466667000000000e+00  4.633334000000000e+00  4.818504000000000e+00
  9.699999999999999e+00  7.380340000000000e+00  6.842135000000000e+00
  4.900000000000000e+00  3.471068000000000e+00  4.080340000000000e+00
  5.809252000000000e+00  4.117360000000000e+00  4.466667000000000e+00
  8.033334000000000e+00  5.918253000000000e+00  5.717083000000000e+00
  1.078034000000000e+01  8.347448999999999e+00  7.600000000000000e+00
  9.800000000000001e+00  7.480340000000000e+00  6.942136000000000e+00
  1.024093000000000e+01  7.866667000000000e+00  7.229663000000000e+00
  1.161850000000000e+01  9.117082999999999e+00  8.234719000000000e+00
  1.364214000000000e+01  1.100000000000000e+01  9.820508999999999e+00
#Scale factor sets=0
#Nodes=0
#Fields=1
1) potential, field, real, #Components=1
 value. l.Lagrange*l.Lagrange*l.Lagrange, no modify, grid based.
 #xi1=3, #xi2=3, #xi3=2
Element: 2
 Values :
  3.000000000000000e+00  4.000000000000000e+00  5.000000000000000e+00  6.000000000000000e+00
  3.440926000000000e+00  4.310351000000000e+00  5.230064000000000e+00  6.175875000000000e+00
  4.818504000000000e+00  5.373787000000000e+00  6.083882000000000e+00  6.881852000000000e+00
  6.842135000000000e+00  7.033333000000000e+00  7.469840000000000e+00  8.060679000000000e+00
  4.080340000000000e+00  4.806672000000000e+00  5.633844000000000e+00  6.515528000000000e+00
  4.466667000000000e+00  5.091606000000000e+00  5.850243000000000e+00  6.683273000000000e+00
  5.717083000000000e+00  6.089969000000000e+00  6.667233000000000e+00  7.366666000000000e+00
  7.600000000000000e+00  7.667177000000000e+00  8.002658000000000e+00  8.512877000000000e+00
  6.942136000000000e+00  7.133333000000000e+00  7.569840000000000e+00  8.160679999999999e+00
  7.229663000000000e+00  7.363398000000000e+00  7.753600000000000e+00  8.307767000000000e+00
  8.234719000000000e+00  8.217217000000000e+00  8.481380000000000e+00  8.933334000000000e+00
  9.820508999999999e+00  9.603173000000000e+00  9.691462000000000e+00  9.994897999999999e+00"""

field_header_3d_template = """#Scale factor sets=0
#Nodes=0
#Fields=1
{0}) {1}, field, real, #Components=1
 value. l.Lagrange*l.Lagrange*l.Lagrange, no modify, grid based.
 #xi1={2}, #xi2={3}, #xi3={4}
"""

field_data_template = """Element: {0}
  Values:
{1}"""

test_template = """Group name: block
Shape.  Dimension=3
#Scale factor sets=0
#Nodes=0
#Fields=2
1) material_type, field, integer, #Components=1
 number. l.Lagrange*l.Lagrange*l.Lagrange, no modify, grid based.
 #xi1=2, #xi2=3, #xi3=2
2) potential, field, real, #Components=1
 value. l.Lagrange*l.Lagrange*l.Lagrange, no modify, grid based.
 #xi1=2, #xi2=3, #xi3=2
Element: 1 0 0
  Values:
  1 1 3
  1 1 3
  1 2 3
  1 2 2
  1 1 3
  1 1 3
  1 2 3
  2 2 2
  1 3 3
  1 3 3
  2 2 3
  2 2 2
  13.5 12.2 10.1
  14.5 12.2 10.1
  15.5 12.2 10.1
  16.5 12.2 10.1
  12.0 11.0 10.0
  13.0 11.0 10.0
  14.0 11.0 10.0
  15.0 11.0 10.0
  10.5 10.7 9.9
  11.5 10.7 9.9
  12.5 10.7 9.9
  13.5 10.7 9.9"""

test_template_2 = """Group name: block
Shape.  Dimension=3
#Scale factor sets=0
#Nodes=0
#Fields=2
1) material_type, field, integer, #Components=1
 number. l.Lagrange*l.Lagrange*l.Lagrange, no modify, grid based.
 #xi1=2, #xi2=3, #xi3=2
2) potential, field, real, #Components=1
 value. l.Lagrange*l.Lagrange*l.Lagrange, no modify, grid based.
 #xi1=2, #xi2=3, #xi3=2
Element: 1 0 0
  Values:
  1 1 3 1 1 3 1 2 3 1 2 2 1 1 3 1 1 3 1 2 3 2 2 2 1 3 3 1 3 3 2 2 3 2 2 2
  13.5 12.2 10.1
  14.5 12.2 10.1
  15.5 12.2 10.1
  16.5 12.2 10.1
  12.0 11.0 10.0
  13.0 11.0 10.0
  14.0 11.0 10.0
  15.0 11.0 10.0
  10.5 10.7 9.9
  11.5 10.7 9.9
  12.5 10.7 9.9
  13.5 10.7 9.9"""

test_template_3 = """Group name: block
Shape.  Dimension=3
#Scale factor sets=0
#Nodes=0
#Fields=1
1) punctum_1, field, real, #Components=1
 number. l.Lagrange*l.Lagrange*l.Lagrange, no modify, grid based.
 #xi1=0, #xi2=3, #xi3=1
Element: 1 0 0
  Values:
  1 1 3 1 4 5 7 1
"""
