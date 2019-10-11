#ifndef CAIRO_FEATURES_H
#define CAIRO_FEATURES_H

#ifdef  __cplusplus
# define CAIRO_BEGIN_DECLS  extern "C" {
# define CAIRO_END_DECLS    }
#else
# define CAIRO_BEGIN_DECLS
# define CAIRO_END_DECLS
#endif

/*#define CAIRO_VERSION_MAJOR 1
#define CAIRO_VERSION_MINOR 16
#define CAIRO_VERSION_MICRO 0

#define CAIRO_VERSION_STRING "1.16.0"*/

#define CAIRO_HAS_FT_FONT 1
#define CAIRO_HAS_WIN32_FONT 0
#define CAIRO_HAS_WIN32_SURFACE 1

#define  COGL_ENABLE_EXPERIMENTAL_2_0_API

#endif