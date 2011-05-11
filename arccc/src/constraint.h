// constraint.h - 

struct constraint;
struct wordvar;
struct lettervar;

typedef enum {
  VALUE_CHANGE,
  VALUE_INSTANTIATION,
} trigger_type;

typedef gboolean (*constraint_function)(struct constraint *c);

// the general form of a constraint
struct constraint {
  constraint_function func;
  gboolean on_queue;
  gint data;
};



// word to letter constraint
struct overlap_constraint {
  constraint_function func;
  gboolean on_queue;
  struct wordvar *w;
  struct lettervar *l;
  int offset; // offset of letter into word
};

// uniqueness constraint
struct uniqueness_constraint {
  constraint_function func;
  gboolean on_queue;
  struct wordvar *w;
  GSList *other_words;
};


struct overlap_constraint *new_overlap_constraint(struct wordvar *w, 
                                                  struct lettervar *l,
                                                  gint offset);

struct uniqueness_constraint *new_uniqueness_constraint(struct wordvar *w,
                                                        GSList *other_words);
