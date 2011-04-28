import xlrd
import numpy as np
from welltools import extract_row, extract_col

DETECT = 'Detect'

def safe_float(s):
    try:
        return float(s)
    except:
        return float('nan')

class Normalization(object):
    '''This object communicates the parameters (including input and output files) for a normalization'''
    def __init__(self):
        self.input_file = ''
        self.output_file = ''
        self.shape = DETECT
        self.detected_384 = False
        self.plate_column = ()
        self.well_column = ()
        self.wellrow_column = ()
        self.wellcol_column = ()
        self.combined_wellrowcol = True
        self.gene_column = ()
        self.num_replicates = 0
        self.replicate_features = {}

        self.file_listeners = []
        self.parsing_listeners = []
        self.feature_selection_listeners = []

    def set_input_file(self, val):
        self.input_file = val
        try:
            self.book = xlrd.open_workbook(self.input_file)
            self.update_file_listeners()
        except:
            # XXX - report error
            pass

    def update_file_listeners(self):
        for f in self.file_listeners:
            f()

    def parsing_finished(self):
        for f in self.parsing_listeners:
            f()

    def feature_selection_finished(self):
        for f in self.feature_selection_listeners:
            f()

    def get_column_values(self, column_specifier):
        # import pdb
        # pdb.set_trace()
        return [cell.value for cell in self.book.sheet_by_index(column_specifier[0]).col(column_specifier[1])[1:]]

    def fetch_plates(self):
        return self.get_column_values(self.plate_column)

    def fetch_rows(self):
        if self.combined_wellrowcol:
            return [extract_row(v) for v in self.get_column_values(self.well_column)]
        else:
            return self.get_column_values(self.wellrow_column)

    def fetch_cols(self):
        if self.combined_wellrowcol:
            return [extract_col(v) for v in self.get_column_values(self.well_column)]
        else:
            return self.get_column_values(self.wellcol_column)

    def fetch_genes(self):
        return self.get_column_values(self.gene_column)

    def ready(self):
        for i in range(self.num_replicates):
            if self.replicate_features.get(i, None) is None:
                return False
        return True

    def set_replicate_feature(self, index, val):
        self.replicate_features[index] = val
        if self.ready():
            self.feature_selection_finished()

    def get_replicate_data(self, repindex):
        return [safe_float(v) for v in self.get_column_values(self.replicate_features[repindex])]

    def num_plates(self):
        return len(set(self.get_column_values(self.plate_column)))

    def plate_names(self):
        return sorted(set(self.get_column_values(self.plate_column)))

    def plate_shape(self):
        if self.shape == DETECT:
            return "384" if self.detected_384 else "96"
        return self.shape

    def plate_dims(self):
        return (16, 24) if self.plate_shape() == "384" else (8, 12)

    def plate_array(self, plate_name, repindex):
        plate_mask = np.array([v == plate_name for v in self.get_column_values(self.plate_column)])
        indices = plate_mask.nonzero()[0]
        rows = np.array([ord(r) - ord('A') for r in self.fetch_rows()])
        cols = np.array([int(c) - 1 for c in self.fetch_cols()])
        vals = np.array(self.get_replicate_data(repindex))
        output = np.zeros(self.plate_dims(), np.float)
        output[rows[indices], cols[indices]] = vals[indices]
        return output
        
        
