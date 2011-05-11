// common.h - 

struct constraint;

GPtrArray *read_words(char *filename);
gchar *read_grid(char *filename, GSList **wordlist, GSList **letterlist, GSList **constraintlist);
void init_vars(GSList *words, GSList *letters, GPtrArray *dictionary);
gboolean run_constraints(void);
void put_constraint_on_queue(struct constraint *c);
void find_solution(GSList *words, GSList *letters, gchar *grid, gint depth);

#define MAX_GRID 128

