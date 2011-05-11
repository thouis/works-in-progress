/* init_vars.c - */

#include <stdio.h>
#include <glib.h>

#include "common.h"
#include "wordvar.h"
#include "lettervar.h"

void
init_vars(GSList *words, GSList *letters, GPtrArray *dictionary)
{
  GSList *p;

  for (p = words; p != NULL; p = p->next) {
    struct wordvar *w = p->data;
    gint i;

    w->possible_values = g_ptr_array_new();

    for (i = 0; i < dictionary->len; i++) {
      gchar *dword = g_ptr_array_index(dictionary, i);
      gint j;

      // check that the lengths match
      if (strlen(dword) != w->length) continue;

      // check that the word matches the constraints
      for (j = 0; j < w->length; j++) {
        if (w->letters[j]->letters_allowed[(guint) dword[j]] != TRUE) break;
      }
      if (j < w->length) continue;
      
      // add this word to the possible values
      g_ptr_array_add(w->possible_values, dword);
      for (j = 0; j < w->length; j++) {
        w->letter_counts[j][(guint) dword[j]]++;
      }
    }

    if (w->possible_values->len == 0) {
      printf("Die: No words for %s.\n", w->name->str);
      exit(-1);
    }
  }

  for (p = letters; p != NULL; p = p->next) {
    struct lettervar *l = p->data;
    gint i, val = 0;
    
    l->num_letters_allowed = 0;
    // update allowed letters
    for (i = 0; i < 256; i++) {
      if ((l->letter_counts[0][i] > 0) && (l->letter_counts[1][i] > 0)) {
        l->letters_allowed[i] = TRUE;
        l->num_letters_allowed++;
        val = i;
      } else {
        l->letters_allowed[i] = FALSE;
      }
    }

    if (l->num_letters_allowed == 0) {
      printf("Die: No letters for %s.\n", l->name->str);
      exit(-1);
    } 
    if (l->num_letters_allowed == 1) {
      *(l->pos) = val;
    }
  }
}
