import re

def extract_row(well):
    well = well.upper().strip()
    if len(well) > 0 and 'A' <= well[0] <= 'P':
        return well[0]
    return '(could not parse row from %s)'%(well)
    
def extract_col(well):
    # find the first block of numbers
    m = re.match('[^0-9]*([0-9]+)', well)
    if m:
        return m.group(1)
    return '(could not parse col from %s)'%(well)
