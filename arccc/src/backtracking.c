/* backtracking.c - */

#include <stdio.h>
#include <glib.h>
#include <string.h>

#include "common.h"
#include "wordvar.h"
#include "lettervar.h"
#include "constraint.h"

static void push_state(GSList *words, GSList *letters);
static void pop_state(GSList *words, GSList *letters);

extern gint total;

void
find_solution(GSList *words, GSList *letters, gchar *grid, gint depth)
{
  GSList *ll;
  gchar gridsnap[MAX_GRID*MAX_GRID];
  static gint count = 0;
  static gint maxdepth = 0;

  count++;
    
  if (depth >= maxdepth) {
    printf("depth %d (%d, %d)\n%s\n\n", maxdepth = depth, count, total, grid);
  }

  push_state(words, letters);
  strcpy(gridsnap, grid);
  
  if (run_constraints() == TRUE) {
    gint min = 257;
    struct lettervar *next_to_try = NULL;
    gboolean letters_to_try[256];
    gint i;
    
    // find the most constrained (but still not set) letter
    for (ll = letters; ll != NULL; ll = ll->next) {
      struct lettervar *l = ll->data;
      
      if (l->num_letters_allowed == 1) continue;

      if (l->num_letters_allowed < min) {
        min = l->num_letters_allowed;
        next_to_try = l;
      }
    }


    if (next_to_try == NULL) {
      total++;
      printf("depth %d (%d, %d)\n%s\n\n", depth, count, total, grid);
      pop_state(words, letters);
      strcpy(grid, gridsnap);
      return;
    }

    memcpy(letters_to_try, next_to_try->letters_allowed, sizeof (letters_to_try));
    memset(next_to_try->letters_allowed, 0, sizeof (letters_to_try));

    
    for (i = 0; i < 256; i++) {
      if (letters_to_try[i]) {
        next_to_try->letters_allowed[i] = TRUE;
        next_to_try->num_letters_allowed = 1;
        
        if (depth == 0) {
          *(next_to_try->pos) = i - 'a' + 'A';
        } else {
          *(next_to_try->pos) = i;
        }
        
        put_constraint_on_queue((struct constraint *) next_to_try->constraints[0]);
        put_constraint_on_queue((struct constraint *) next_to_try->constraints[1]);
        find_solution(words, letters, grid, depth + 1);

        next_to_try->letters_allowed[i] = FALSE;
      }
    }
  }

  pop_state(words, letters);
  strcpy(grid, gridsnap);
}

static void
push_state(GSList *words, GSList *letters)
{
  GSList *p;
  GSList *newwords = NULL, *newletters = NULL;
  
  for (p = words; p != NULL; p = p->next) {
    struct wordvar *w = p->data;
    g_ptr_array_add(w->stack, (void *) w->possible_values->len);
  }
  
  for (p = letters; p != NULL; p = p->next) {
    struct lettervar *l = p->data;
    g_array_append_vals(l->stack, l, 1);
  }
}

static void
pop_state(GSList *words, GSList *letters)
{
  GSList *p;

  for (p = words; p != NULL; p = p->next) {
    struct wordvar *w = p->data;
    w->possible_values->len = (guint) g_ptr_array_index(w->stack, w->stack->len-1);
    g_ptr_array_set_size(w->stack, w->stack->len-1);
  }

  for (p = letters; p != NULL; p = p->next) {
    struct lettervar *l = p->data;
    *l = g_array_index(l->stack, struct lettervar, l->stack->len-1);
    g_array_set_size(l->stack, l->stack->len-1);
  }
}
