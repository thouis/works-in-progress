import MySQLdb

conn = MySQLdb.connect('ptilouis', 'biophenics', 'biophenics', 'biophenics')
cursor = conn.cursor()

chemicals = {}


cursor.execute('SELECT PLATE_ID,PLATE_NAME,WELL_ROW_LABEL, WELL_COL_LABEL FROM WELL NATURAL JOIN PLATE WHERE PLATE_ID IN (6150, 6151, 6152, 6153, 6162)')
for key in cursor.fetchall():
    chemicals[key] = 'EMPTY'


cursor.execute('SELECT PLATE_ID,PLATE_NAME,WELL_ROW_LABEL, WELL_COL_LABEL, CHEMICAL_NAME FROM WELL NATURAL JOIN CHEMICAL_WELL NATURAL JOIN CHEMICAL NATURAL JOIN PLATE WHERE PLATE_ID IN (6150, 6151, 6152, 6153, 6162)')

for plate_id, plate_name, row, col, chemical in cursor.fetchall():
    key = (plate_id, plate_name, row, col)
    if chemicals[key] in ('DMSO', 'EMPTY'):
        chemicals[key] = chemical

for (plate_id, plate_name, row, col), chemical in sorted(chemicals.iteritems()):
    print "%s\t%s\t%s\t%s\t%s"%(plate_id, plate_name, row, col, chemical)

