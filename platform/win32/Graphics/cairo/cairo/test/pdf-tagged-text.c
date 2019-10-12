/*
 * Copyright © 2016 Adrian Johnson
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 * Author: Adrian Johnson <ajohnson@redneon.com>
 */

#include "cairo-test.h"

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include <cairo.h>
#include <cairo-pdf.h>

/* This test checks PDF with
 * - tagged text
 * - hyperlinks
 * - document outline
 * - metadata
 * - thumbnails
 * - page labels
 */

#define BASENAME "pdf-tagged-text.out"

#define PAGE_WIDTH 595
#define PAGE_HEIGHT 842

#define HEADING1_SIZE 16
#define HEADING2_SIZE 14
#define HEADING3_SIZE 12
#define TEXT_SIZE 12
#define HEADING_HEIGHT 50
#define MARGIN 50

struct section {
    int level;
    const char *heading;
    int num_paragraphs;
};

static const struct section contents[] = {
    { 0, "Chapter 1",     1 },
    { 1, "Section 1.1",   4 },
    { 2, "Section 1.1.1", 3 },
    { 1, "Section 1.2",   2 },
    { 2, "Section 1.2.1", 4 },
    { 2, "Section 1.2.2", 4 },
    { 1, "Section 1.3",   2 },
    { 0, "Chapter 2",     1 },
    { 1, "Section 2.1",   4 },
    { 2, "Section 2.1.1", 3 },
    { 1, "Section 2.2",   2 },
    { 2, "Section 2.2.1", 4 },
    { 2, "Section 2.2.2", 4 },
    { 1, "Section 2.3",   2 },
    { 0, "Chapter 3",     1 },
    { 1, "Section 3.1",   4 },
    { 2, "Section 3.1.1", 3 },
    { 1, "Section 3.2",   2 },
    { 2, "Section 3.2.1", 4 },
    { 2, "Section 3.2.2", 4 },
    { 1, "Section 3.3",   2 },
    { 0, NULL }
};

static const char *ipsum_lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing"
    " elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
    " Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi"
    " ut aliquip ex ea commodo consequat. Duis aute irure dolor in"
    " reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla"
    " pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa"
    " qui officia deserunt mollit anim id est laborum.";

static const char *roman_numerals[] = {
    "i", "ii", "iii", "iv", "v"
};

#define MAX_PARAGRAPH_LINES 20

static int paragraph_num_lines;
static char *paragraph_text[MAX_PARAGRAPH_LINES];
static double paragraph_height;
static double line_height;
static double y_pos;
static int outline_parents[10];
static int page_num;

static void
layout_paragraph (cairo_t *cr)
{
    char *text, *begin, *end, *prev_end;
    cairo_text_extents_t text_extents;
    cairo_font_extents_t font_extents;

    cairo_select_font_face (cr, "Serif", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size(cr, TEXT_SIZE);
    cairo_font_extents (cr, &font_extents);
    line_height = font_extents.height;
    paragraph_height = 0;
    paragraph_num_lines = 0;
    text = strdup (ipsum_lorem);
    begin = text;
    end = text;
    prev_end = end;
    while (*begin) {
	end = strchr(end, ' ');
	if (!end) {
	    paragraph_text[paragraph_num_lines++] = strdup (begin);
	    break;
	}
	*end = 0;
	cairo_text_extents (cr, begin, &text_extents);
	*end = ' ';
	if (text_extents.width + 2*MARGIN > PAGE_WIDTH) {
	    int len = prev_end - begin;
	    char *s = malloc (len);
	    memcpy (s, begin, len);
	    s[len-1] = 0;
	    paragraph_text[paragraph_num_lines++] = s;
	    begin = prev_end + 1;
	}
	prev_end = end;
	end++;
    }
    paragraph_height = line_height * (paragraph_num_lines + 1);
    free (text);
}

static void
draw_paragraph (cairo_t *cr)
{
    int i;

    cairo_select_font_face (cr, "Serif", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size(cr, TEXT_SIZE);
    cairo_tag_begin (cr, "P", NULL);
    for (i = 0; i < paragraph_num_lines; i++) {
	cairo_move_to (cr, MARGIN, y_pos);
	cairo_show_text (cr, paragraph_text[i]);
	y_pos += line_height;
    }
    cairo_tag_end (cr, "P");
    y_pos += line_height;
}

static void
draw_page_num (cairo_surface_t *surface, cairo_t *cr, const char *prefix, int num)
{
    char buf[100];

    buf[0] = 0;
    if (prefix)
	strcat (buf, prefix);

    if (num)
	sprintf (buf + strlen(buf), "%d", num);

    cairo_save (cr);
    cairo_select_font_face (cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size(cr, 12);
    cairo_move_to (cr, PAGE_WIDTH/2, PAGE_HEIGHT - MARGIN);
    cairo_show_text (cr, buf);
    cairo_restore (cr);
    cairo_pdf_surface_set_page_label (surface, buf);
}

static void
draw_contents (cairo_surface_t *surface, cairo_t *cr, const struct section *section)
{
    char buf[100];

    sprintf(buf, "dest='%s'", section->heading);
    cairo_select_font_face (cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
    switch (section->level) {
	case 0:
	    cairo_set_font_size(cr, HEADING1_SIZE);
	    break;
	case 1:
	    cairo_set_font_size(cr, HEADING2_SIZE);
	    break;
	case 2:
	    cairo_set_font_size(cr, HEADING3_SIZE);
	    break;
    }

    if (y_pos + HEADING_HEIGHT + MARGIN > PAGE_HEIGHT) {
	cairo_show_page (cr);
	draw_page_num (surface, cr, roman_numerals[page_num++], 0);
	y_pos = MARGIN;
    }
    cairo_move_to (cr, MARGIN, y_pos);
    cairo_save (cr);
    cairo_set_source_rgb (cr, 0, 0, 1);
    cairo_tag_begin (cr, "TOCI", NULL);
    cairo_tag_begin (cr, "Reference", NULL);
    cairo_tag_begin (cr, CAIRO_TAG_LINK, buf);
    cairo_show_text (cr, section->heading);
    cairo_tag_end (cr, CAIRO_TAG_LINK);
    cairo_tag_end (cr, "Reference");
    cairo_tag_end (cr, "TOCI");
    cairo_restore (cr);
    y_pos += HEADING_HEIGHT;
}

static void
draw_section (cairo_surface_t *surface, cairo_t *cr, const struct section *section)
{
    int flags, i;
    char buf[100];
    char buf2[100];

    cairo_tag_begin (cr, "Sect", NULL);
    sprintf(buf, "name='%s'", section->heading);
    sprintf(buf2, "dest='%s'", section->heading);
    cairo_select_font_face (cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD);
    if (section->level == 0) {
	cairo_show_page (cr);
	draw_page_num (surface, cr, NULL, page_num++);
	cairo_set_font_size(cr, HEADING1_SIZE);
	cairo_move_to (cr, MARGIN, MARGIN);
	cairo_tag_begin (cr, "H1", NULL);
	cairo_tag_begin (cr, CAIRO_TAG_DEST, buf);
	cairo_show_text (cr, section->heading);
	cairo_tag_end (cr, CAIRO_TAG_DEST);
	cairo_tag_end (cr, "H1");
	y_pos = MARGIN + HEADING_HEIGHT;
	flags = CAIRO_PDF_OUTLINE_FLAG_BOLD | CAIRO_PDF_OUTLINE_FLAG_OPEN;
	outline_parents[0] = cairo_pdf_surface_add_outline (surface,
							    CAIRO_PDF_OUTLINE_ROOT,
							    section->heading,
							    buf2,
							    flags);
    } else {
	if (section->level == 1) {
	    cairo_set_font_size(cr, HEADING2_SIZE);
	    flags = 0;
	} else {
	    cairo_set_font_size(cr, HEADING3_SIZE);
	    flags = CAIRO_PDF_OUTLINE_FLAG_ITALIC;
	}

	if (y_pos + HEADING_HEIGHT + paragraph_height + MARGIN > PAGE_HEIGHT) {
	    cairo_show_page (cr);
	    draw_page_num (surface, cr, NULL, page_num++);
	    y_pos = MARGIN;
	}
	cairo_move_to (cr, MARGIN, y_pos);
	if (section->level == 1)
	    cairo_tag_begin (cr, "H2", NULL);
	else
	    cairo_tag_begin (cr, "H3", NULL);
	cairo_tag_begin (cr, CAIRO_TAG_DEST, buf);
	cairo_show_text (cr, section->heading);
	cairo_tag_end (cr, CAIRO_TAG_DEST);
	if (section->level == 1)
	    cairo_tag_end (cr, "H2");
	else
	    cairo_tag_end (cr, "H3");
	y_pos += HEADING_HEIGHT;
	outline_parents[section->level] = cairo_pdf_surface_add_outline (surface,
									 outline_parents[section->level - 1],
									 section->heading,
									 buf2,
									 flags);
    }

    for (i = 0; i < section->num_paragraphs; i++) {
	if (y_pos + paragraph_height + MARGIN > PAGE_HEIGHT) {
	    cairo_show_page (cr);
	    draw_page_num (surface, cr, NULL, page_num++);
		y_pos = MARGIN;
	}
	draw_paragraph (cr);
    }
    cairo_tag_end (cr, "Sect");
}

static void
draw_cover (cairo_surface_t *surface, cairo_t *cr)
{
    cairo_select_font_face (cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD);
    cairo_set_font_size(cr, 16);
    cairo_move_to (cr, PAGE_WIDTH/3, PAGE_HEIGHT/2);
    cairo_tag_begin (cr, "Span", NULL);
    cairo_show_text (cr, "PDF Features Test");
    cairo_tag_end (cr, "Span");

    draw_page_num (surface, cr, "cover", 0);
}

static void
create_document (cairo_surface_t *surface, cairo_t *cr)
{
    layout_paragraph (cr);

    cairo_pdf_surface_set_thumbnail_size (surface, PAGE_WIDTH/10, PAGE_HEIGHT/10);

    cairo_pdf_surface_set_metadata (surface, CAIRO_PDF_METADATA_TITLE, "PDF Features Test");
    cairo_pdf_surface_set_metadata (surface, CAIRO_PDF_METADATA_AUTHOR, "cairo test suite");
    cairo_pdf_surface_set_metadata (surface, CAIRO_PDF_METADATA_SUBJECT, "cairo test");
    cairo_pdf_surface_set_metadata (surface, CAIRO_PDF_METADATA_KEYWORDS,
				    "tags, links, outline, page labels, metadata, thumbnails");
    cairo_pdf_surface_set_metadata (surface, CAIRO_PDF_METADATA_CREATOR, "pdf-features");
    cairo_pdf_surface_set_metadata (surface, CAIRO_PDF_METADATA_CREATE_DATE, "2016-01-01T12:34:56+10:30");
    cairo_pdf_surface_set_metadata (surface, CAIRO_PDF_METADATA_MOD_DATE, "2016-06-21T05:43:21Z");

    cairo_tag_begin (cr, "Document", NULL);

    draw_cover (surface, cr);
    cairo_pdf_surface_add_outline (surface,
				   CAIRO_PDF_OUTLINE_ROOT,
				   "Cover", "page=1",
                                   CAIRO_PDF_OUTLINE_FLAG_BOLD);
    cairo_show_page (cr);

    page_num = 0;
    draw_page_num (surface, cr, roman_numerals[page_num++], 0);
    y_pos = MARGIN;

    cairo_pdf_surface_add_outline (surface,
				   CAIRO_PDF_OUTLINE_ROOT,
				   "Contents", "dest='TOC'",
                                   CAIRO_PDF_OUTLINE_FLAG_BOLD);

    cairo_tag_begin (cr, CAIRO_TAG_DEST, "name='TOC' internal");
    cairo_tag_begin (cr, "TOC", NULL);
    const struct section *sect = contents;
    while (sect->heading) {
	draw_contents (surface, cr, sect);
	sect++;
    }
    cairo_tag_end (cr, "TOC");
    cairo_tag_end (cr, CAIRO_TAG_DEST);

    page_num = 1;
    sect = contents;
    while (sect->heading) {
	draw_section (surface, cr, sect);
	sect++;
    }

    cairo_tag_end (cr, "Document");
}

static cairo_test_status_t
preamble (cairo_test_context_t *ctx)
{
    cairo_surface_t *surface;
    cairo_t *cr;
    cairo_status_t status, status2;
    char *filename;
    const char *path = cairo_test_mkdir (CAIRO_TEST_OUTPUT_DIR) ? CAIRO_TEST_OUTPUT_DIR : ".";

    if (! cairo_test_is_target_enabled (ctx, "pdf"))
	return CAIRO_TEST_UNTESTED;

    xasprintf (&filename, "%s/%s.pdf", path, BASENAME);
    surface = cairo_pdf_surface_create (filename, PAGE_WIDTH, PAGE_HEIGHT);

    cr = cairo_create (surface);
    create_document (surface, cr);

    status = cairo_status (cr);
    cairo_destroy (cr);
    cairo_surface_finish (surface);
    status2 = cairo_surface_status (surface);
    if (status != CAIRO_STATUS_SUCCESS)
	status = status2;

    cairo_surface_destroy (surface);
    if (status) {
	cairo_test_log (ctx, "Failed to create pdf surface for file %s: %s\n",
			filename, cairo_status_to_string (status));
	return CAIRO_TEST_FAILURE;
    }

    free (filename);

    return CAIRO_TEST_SUCCESS;
}

CAIRO_TEST (pdf_tagged_text,
	    "Check tagged text, hyperlinks and PDF document features",
	    "pdf", /* keywords */
	    NULL, /* requirements */
	    0, 0,
	    preamble, NULL)
