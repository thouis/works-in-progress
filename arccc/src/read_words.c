/* read_words.c - */

#include <stdio.h>
#include <glib.h>

#include "common.h"

GPtrArray *
read_words(char *filename)
{
  FILE *fp = fopen(filename, "r");
  gchar buf[128];
  GPtrArray *out;
  GStringChunk *chunk;

  g_assert(fp != NULL);
  
  out = g_ptr_array_new();
  chunk = g_string_chunk_new(1024); // about 20 strings

  while(fgets(buf, sizeof(buf), fp) != NULL) {
    g_strchomp(buf); // remove trailing newline
    if (*buf == '#') continue;
    if ((*buf >= 'A') && (*buf <= 'Z')) continue;
    g_ptr_array_add(out, g_string_chunk_insert(chunk, buf));
  }

  fclose(fp);

  return (out);
}
