// lettervar.h - 

struct overlap_constraint;


// constraint between a letter square and one word in that position
struct lettervar {
  gint letter_counts[2][256]; // support for each letter from the across=0 or down=1 words
  gboolean letters_allowed[256]; // letters that can appear in this word
  gint num_letters_allowed;
  struct overlap_constraint *constraints[2];
  GArray *stack; // for backtracking
  GString *name;
  gchar *pos;
};
