// wordvar.h - 

struct lettervar;

struct wordvar {
  GPtrArray *possible_values;
  gint length; // length of this word
  struct lettervar **letters;
  gint **letter_counts; // dimensions are [length][256] (pointers into lettervars)
  GPtrArray *stack; // for backtracking
  struct overlap_constraint **orthogonal_constraints;
  struct uniqueness_constraint *unique_constraint;
  GString *name;
};
