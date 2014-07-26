/**
 * Copyright (C) 2008 John Millikin. See LICENSE.txt for details.
 * Author: John Millikin <jmillikin@gmail.com>
 * Enhancements by: Alec Flett <alecf@flett.org>
 * 
 * Implementation of jsonlib2.
**/

/* includes {{{ */
#include <Python.h>
#include <stddef.h>
#include <stdio.h>
#include <ctype.h>
#include <math.h>

#define FALSE 0
#define TRUE 1

#ifndef Py_NAN
#define Py_NAN (Py_HUGE_VAL *0.)
#endif

#if PY_VERSION_HEX < 0x02050000
typedef int Py_ssize_t;
#endif
/* }}} */

/* util declarations {{{ */
static PyObject *
jsonlib_import (const char *module_name, const char *obj_name);

static PyObject *
jsonlib_str_format (const char *tmpl, PyObject *args);

static size_t
next_power_2 (size_t start, size_t min);
/* }}} */

/* parser declarations {{{ */
enum
{
	UTF_8 = 0,
	UTF_8_BOM,
	UTF_16_LE,
	UTF_16_LE_BOM,
	UTF_16_BE,
	UTF_16_BE_BOM,
	UTF_32_LE,
	UTF_32_LE_BOM,
	UTF_32_BE,
	UTF_32_BE_BOM
};

#define BOM_UTF8     "\xef\xbb\xbf"
#define BOM_UTF16_LE "\xff\xfe"
#define BOM_UTF16_BE "\xfe\xff"
#define BOM_UTF32_LE "\xff\xfe\x00\x00"
#define BOM_UTF32_BE "\x00\x00\xfe\xff"

typedef struct _Decoder {
	Py_UNICODE *start;
	Py_UNICODE *end;
	Py_UNICODE *index;
	
	Py_UNICODE *stringparse_buffer;
	size_t stringparse_buffer_size;

    PyObject* infinity;
    PyObject* neg_infinity;
    PyObject* nan;

    // borrowed refs
    PyObject* parse_float;
    PyObject* parse_int;
    PyObject* parse_constant;
} Decoder;

typedef enum
{
	ARRAY_EMPTY,
	ARRAY_NEED_VALUE,
	ARRAY_GOT_VALUE
} ParseArrayState;

typedef enum
{
	OBJECT_EMPTY,
	OBJECT_NEED_KEY,
	OBJECT_NEED_COLON,
	OBJECT_NEED_VALUE,
	OBJECT_GOT_VALUE
} ParseObjectState;

static PyObject *ReadError;

static PyObject *read_string (Decoder *decoder);
static PyObject *read_number (Decoder *decoder);
static PyObject *read_array (Decoder *decoder);
static PyObject *read_object (Decoder *decoder);
static PyObject *json_read (Decoder *decoder);
/* }}} */

/* serializer declarations {{{ */
typedef struct _Encoder Encoder;
struct _Encoder
{
	/* Pulled from the current interpreter to avoid errors when used
	 * with sub-interpreters.
	**/
	PyObject *UserString;
	
	/* Options passed to _write */
	int sort_keys;
	PyObject *indent_string;
	int ensure_ascii;
	int coerce_keys;
    int escape_slash;           /* escape the '/' character? */
    int check_circular;
	PyObject *default_handler;
    int allow_nan;
	
	int (*append_ascii) (Encoder *, const char *, const size_t);
	int (*append_unicode) (Encoder *, PyObject *);
	
	/* Constants, saved to avoid lookup later */
	PyObject *true_str;
	PyObject *false_str;
	PyObject *null_str;
	PyObject *inf_str;
	PyObject *neg_inf_str;
	PyObject *nan_str;
	PyObject *quote;
	PyObject *colon;
    PyObject *comma;
};

typedef struct _BufferEncoder
{
	Encoder encoder;
	Py_UNICODE *buffer;
	size_t buffer_size;
	size_t buffer_max_size;
} BufferEncoder;

typedef struct _StreamEncoder
{
	Encoder encoder;
	PyObject *stream;
	char *encoding;
} StreamEncoder;

static const char *hexdigit = "0123456789abcdef";
#define INITIAL_BUFFER_SIZE 32

static PyObject *WriteError;
static PyObject *UnknownSerializerError;

/* Functions for writing actual bytes to a buffer or stream {{{ */
static int
buffer_encoder_append_ascii (Encoder *encoder,
                             const char *text,
                             const size_t len);

static int
buffer_encoder_append_unicode (Encoder *encoder,
                               PyObject *text);

static int
stream_encoder_append_ascii (Encoder *encoder,
                             const char *text,
                             const size_t len);

static int
stream_encoder_append_unicode (Encoder *encoder,
                               PyObject *text);

static int
encoder_append_string (Encoder *encoder, PyObject *text);

static int
buffer_encoder_resize (BufferEncoder *encoder, size_t delta);
/* }}} */


static PyObject *
ascii_constant (const char *value, int len);

static int
write_object (Encoder *encoder, PyObject *object, int indent_level,
              int in_unknown_hook);

static int
write_iterable (Encoder *encoder, PyObject *iterable, int indent_level);

static int
write_mapping (Encoder *encoder, PyObject *mapping, int indent_level);

static PyObject *
write_basic (Encoder *encoder, PyObject *value);

static PyObject *
write_string (Encoder *encoder, PyObject *string);

static PyObject *
write_unicode (Encoder *encoder, PyObject *unicode);

static PyObject *
unicode_to_unicode (PyObject *unicode, int escape_slash);

static PyObject *
unicode_to_ascii (PyObject *unicode, int escape_slash);
/* }}} */

/* util function definitions {{{ */
static PyObject *
jsonlib_import (const char *module_name, const char *obj_name)
{
	PyObject *module, *obj = NULL;
	if ((module = PyImport_ImportModule (module_name)))
	{
		obj = PyObject_GetAttrString (module, obj_name);
		Py_DECREF (module);
	}
	return obj;
}

static PyObject *
jsonlib_str_format (const char *c_tmpl, PyObject *args)
{
	PyObject *template, *retval;
	
	if (!args) return NULL;
	if (!(template = PyString_FromString (c_tmpl))) return NULL;
	retval = PyString_Format (template, args);
	Py_DECREF (template);
	Py_DECREF (args);
	return retval;
}

static size_t
next_power_2 (size_t start, size_t min)
{
	while (start < min) start <<= 1;
	return start;
}
static PyObject*
normalize_indent_string(PyObject* indent_string)
{
    if (PyInt_Check(indent_string)) {
        long indent_val = PyInt_AsLong(indent_string);
        if (indent_val == -1 && PyErr_Occurred())
            return NULL;

        PyObject* space = ascii_constant(" ", 1);
        PyObject* new_string = PySequence_Repeat(space, indent_val);
        if (new_string) {
            Py_DECREF(space);
            Py_DECREF(indent_string);
            return new_string;
        } else {
            return NULL;
        }
    }
    return indent_string;
}

/* }}} */

/* parser {{{ */
static void
skip_spaces (Decoder *decoder)
{
	/* Don't use Py_UNICODE_ISSPACE, because it returns TRUE for
	 * codepoints that are not valid JSON whitespace.
	**/
	Py_UNICODE c;
	while ((c = (*decoder->index)) && (
	        c == '\x09' ||
	        c == '\x0A' ||
	        c == '\x0D' ||
	        c == '\x20'
	))
		decoder->index++;
}

static int
parser_find_next_value (Decoder *decoder)
{
	/* Return codes:
	 * 
	 * 0 = found atom or value
	 * 1 = found non-value
	**/
	Py_UNICODE *c = decoder->index;
	switch (c[0])
	{
		case '"':
		case '-':
		case '0':
		case '1':
		case '2':
		case '3':
		case '4':
		case '5':
		case '6':
		case '7':
		case '8':
		case '9':
		case '[':
		case '{':
			return 0;
            /* ugh, is there no Py_UNICODE_strncmp ? */
		case 't':               /* true */
			if (c[1] == 'r' && c[2] == 'u' && c[3] == 'e')
				return 0;
		case 'f':               /* false */
			if (c[1] == 'a' && c[2] == 'l' && c[3] == 's' && c[4] == 'e')
				return 0;
		case 'n':               /* null */
			if (c[1] == 'u' && c[2] == 'l' && c[3] == 'l')
				return 0;

        case 'I':               /* Infinity */
            if (c[1] == 'n' && c[2] == 'f' && c[3] == 'i' && c[4] == 'n' &&
                c[5] == 'i' && c[6] == 't' && c[7] == 'y')
                return 0;

        case 'N':
            if (c[1] == 'a' && c[2] == 'N')
                return 0;
        
		default:
			return 1;
	}
}

static Py_UCS4
next_ucs4 (Py_UNICODE *index)
{
	unsigned long value = index[0];
	if (value >= 0xD800 && value <= 0xDBFF)
	{
		unsigned long upper = value, lower = index[1];
		
		if (lower)
		{
			upper -= 0xD800;
			lower -= 0xDC00;
			value = ((upper << 10) + lower) + 0x10000;
		}
	}
	return value;
}

static void
count_row_column (Py_UNICODE *start, Py_UNICODE *pos, unsigned long *offset,
                  unsigned long *row, unsigned long *column)
{
	Py_UNICODE *ptr;
	*offset = (pos - start);
	*row = 1;
	
	/* Count newlines in chars < pos */
	for (ptr = start; ptr < pos; ptr++)
	{
		if (*ptr == '\n') (*row)++;
	}
	
	if (*row == 1)
	{
		*column = *offset + 1;
	}
	else
	{
		ptr--;
		/* Loop backwards to find the column */
		while (ptr > start && *ptr != '\n') ptr--;
		*column = (pos - ptr);
	}
}

static void
set_error (Decoder *decoder, Py_UNICODE *position, PyObject *description,
           PyObject *description_args)
{
	const char *tmpl = "JSON parsing error at line %d, column %d"
	                   " (position %d): %s";
	unsigned long row, column, char_offset;
	PyObject *err_str, *err_str_tmpl, *err_format_args;
	
	Py_INCREF (description);
	
	if (description_args)
	{
		PyObject *new_desc;
		new_desc = PyString_Format (description, description_args);
		Py_DECREF (description);
		if (!new_desc) return;
		description = new_desc;
	}
	
	count_row_column (decoder->start, position, &char_offset,
	                  &row, &column);
	
	err_str_tmpl = PyString_FromString (tmpl);
	if (err_str_tmpl)
	{
		err_format_args = Py_BuildValue ("(kkkO)", row, column,
		                                 char_offset, description);
		if (err_format_args)
		{
			err_str = PyString_Format (err_str_tmpl, err_format_args);
			if (err_str)
			{
				PyErr_SetObject (ReadError, err_str);
				Py_DECREF (err_str);
			}
			Py_DECREF (err_format_args);
		}
		Py_DECREF (err_str_tmpl);
	}
	Py_DECREF (description);
}

static void
set_error_simple (Decoder *decoder, Py_UNICODE *position,
                  const char *description)
{
	PyObject *desc_obj;
	desc_obj = PyString_FromString (description);
	if (desc_obj)
	{
		set_error (decoder, position, desc_obj, NULL);
		Py_DECREF (desc_obj);
	}
}

static void
set_error_unexpected (Decoder *decoder, Py_UNICODE *position,
                      const char *wanted)
{
	PyObject *err_str, *err_format_args;
	Py_UCS4 c = next_ucs4 (position);
	
	if (wanted)
	{
		if (c > 0xFFFF)
			err_str = PyString_FromString ("Unexpected U+%08X while looking for %s.");
		else if (c >= 0x008F)
			err_str = PyString_FromString ("Unexpected U+%04X while looking for %s.");
        else
			err_str = PyString_FromString ("Unexpected U+%04X (%c) while looking for %s.");
	}
	else
	{
		if (c > 0xFFFF)
			err_str = PyString_FromString ("Unexpected U+%08X.");
		else if (c >= 0x008F)
            err_str = PyString_FromString("Unexpected U+%04X.");
        else
			err_str = PyString_FromString ("Unexpected U+%04X (%c).");
	}
	
	if (err_str)
	{
		if (wanted)
            if (c >= 0x008F)
                err_format_args = Py_BuildValue ("(ks)", c, wanted);
            else
                err_format_args = Py_BuildValue ("(kcs)", c, c, wanted);
		else if (c >= 0x008F)
            err_format_args = Py_BuildValue ("(k)", c);
        else
			err_format_args = Py_BuildValue ("(kc)", c, c);
        
		if (err_format_args)
		{
			set_error (decoder, position, err_str, err_format_args);
			Py_DECREF (err_format_args);
		}
		Py_DECREF (err_str);
	}
}

static PyObject *
keyword_compare (Decoder *decoder, const char *expected, size_t len,
                 PyObject *retval)
{
	size_t ii, left;
	
	left = decoder->end - decoder->index;
	if (left >= len)
	{
		for (ii = 0; ii < len; ii++)
		{
			if (decoder->index[ii] != (unsigned char)(expected[ii]))
				return NULL;
		}

        if (decoder->parse_constant) {
            PyObject *unicode_constant =
                PyUnicode_FromUnicode(decoder->index, len);
            if (!unicode_constant)
                return NULL;

            PyObject *args = PyTuple_Pack(1, unicode_constant);
            Py_DECREF(unicode_constant);
            if (!args)
                return NULL;

            PyObject *object =
                PyObject_CallObject(decoder->parse_constant, args);
            Py_DECREF(args);

            if (!object)
                return NULL;

            retval = object;
        }
        
		decoder->index += len;
		Py_INCREF (retval);
		return retval;
	}
	return NULL;
}

static int
read_4hex (Py_UNICODE *start, Py_UNICODE *retval_ptr)
{
	PyObject *py_long;
	
	py_long = PyLong_FromUnicode (start, 4, 16);
	if (!py_long) return FALSE;
	
	(*retval_ptr) = (Py_UNICODE) (PyLong_AsUnsignedLong (py_long));
	Py_DECREF (py_long);
	return TRUE;
}

static int
read_unicode_escape (Decoder *decoder, Py_UNICODE *string_start,
                     Py_UNICODE *buffer, size_t *buffer_idx,
                     size_t *index_ptr, size_t max_char_count)
{
	size_t remaining;
	Py_UNICODE value;
	
	(*index_ptr)++;
	
	remaining = max_char_count - (*index_ptr);
	
	if (remaining < 4)
	{
		set_error_simple (decoder, decoder->index + (*index_ptr) - 1,
		                  "Unterminated unicode escape.");
		return FALSE;
	}
	
	if (!read_4hex (string_start + (*index_ptr), &value))
		return FALSE;
		
	(*index_ptr) += 4;
	
	/* Check for surrogate pair */
	if (0xD800 <= value && value <= 0xDBFF)
	{
		Py_UNICODE upper = value, lower;
		
		if (remaining < 10)
		{
			set_error_simple (decoder, decoder->index + (*index_ptr) + 1,
			                  "Missing surrogate pair half.");
			return FALSE;
		}
		
		if (string_start[(*index_ptr)] != '\\' ||
		    string_start[(*index_ptr) + 1] != 'u')
		{
			set_error_simple (decoder, decoder->index + (*index_ptr) + 1,
			                  "Missing surrogate pair half.");
			return FALSE;
		}
		(*index_ptr) += 2;
		
		if (!read_4hex (string_start + (*index_ptr), &lower))
			return FALSE;
			
		(*index_ptr) += 4;
		
#		ifdef Py_UNICODE_WIDE
			upper -= 0xD800;
			lower -= 0xDC00;
			
			/* Merge upper and lower components */
			value = ((upper << 10) + lower) + 0x10000;
			buffer[*buffer_idx] = value;
#		else
			/* No wide character support, return surrogate pairs */
			buffer[(*buffer_idx)++] = upper;
			buffer[*buffer_idx] = lower;
#		endif
	}
	else if (0xDC00 <= value && value <= 0xDFFF)
	{
		PyObject *err_str, *err_format_args;
		Py_UNICODE *position = decoder->index + (*index_ptr) - 5;

		err_str = PyString_FromString ("U+%04X is a reserved code point.");

		if (err_str)
		{
			err_format_args = Py_BuildValue ("(k)", value);
			if (err_format_args)
			{
				set_error (decoder, position, err_str, err_format_args);
				Py_DECREF (err_format_args);
			}
			Py_DECREF (err_str);
		}
		return FALSE;
	}
	else
	{
		buffer[*buffer_idx] = value;
	}
	return TRUE;
}

static PyObject *
read_string_full (Decoder *decoder, Py_UNICODE *start, size_t max_char_count)
{
	PyObject *unicode;
	int escaped = FALSE;
	Py_UNICODE c, *buffer;
	size_t ii, buffer_idx;
	
	/* Allocate enough to hold the worst case */
	buffer = decoder->stringparse_buffer;
	if (max_char_count > decoder->stringparse_buffer_size)
	{
		size_t new_size, existing_size;
		existing_size = decoder->stringparse_buffer_size;
		new_size = next_power_2 (1, max_char_count);
		decoder->stringparse_buffer = PyMem_Resize (buffer, Py_UNICODE, new_size);
		buffer = decoder->stringparse_buffer;
		decoder->stringparse_buffer_size = new_size;
	}
	
	/* Scan through the string, adding values to the buffer as
	 * appropriate.
	**/
	escaped = FALSE;
	buffer_idx = 0;
	for (ii = 0; ii < max_char_count; ii++)
	{
		c = start[ii];
		assert (c != 0);
		
		if (escaped)
		{
			switch (c)
			{
				case '\\':
				case '"':
				case '/':
					buffer[buffer_idx] = c;
					break;
				case 'b': buffer[buffer_idx] = 0x08; break;
				case 'f': buffer[buffer_idx] = 0x0C; break;
				case 'n': buffer[buffer_idx] = 0x0A; break;
				case 'r': buffer[buffer_idx] = 0x0D; break;
				case 't': buffer[buffer_idx] = 0x09; break;
				case 'u':
				{
					size_t next_ii = ii;
					if (read_unicode_escape (decoder, start,
					                         buffer,
					                         &buffer_idx,
					                         &next_ii,
					                         max_char_count))
					{
						ii = next_ii - 1;
					}
					
					else
					{
						return NULL;
					}
					break;
				}
				
				default:
				{
					PyObject *err = NULL, *err_args = NULL;
					err = PyString_FromString ("Unknown escape code: \\%s.");
					err_args = Py_BuildValue ("(u#)", &c, 1);
					if (err && err_args)
					{
						set_error (decoder, start + ii - 1,
						           err, err_args);
					}
					Py_XDECREF (err);
					Py_XDECREF (err_args);
					return NULL;
				}
			}
			escaped = FALSE;
			buffer_idx += 1;
		}
		
		else
		{
			if (c == '\\') escaped = TRUE;
			else if (c == '"') break;
			else
			{
				buffer[buffer_idx] = c;
				buffer_idx += 1;
			}
		}
	}
	
	unicode = PyUnicode_FromUnicode (buffer, buffer_idx);
	
	if (unicode)
	{
		decoder->index = start + max_char_count + 1;
	}
	
	return unicode;
}

static PyObject *
read_string (Decoder *decoder)
{
	PyObject *unicode;
	int escaped = FALSE, fancy = FALSE;
	Py_UNICODE c, *start;
	size_t ii;
	
	/* Start at 1 to skip first double quote. */
	start = decoder->index + 1;
	
	/* Fast case for empty string */
	if (start[0] == '"')
	{
		decoder->index = start + 1;
		return PyUnicode_FromUnicode (NULL, 0);
	}
	
	/* Scan through for maximum character count, and to ensure the string
	 * is terminated.
	**/
	for (ii = 0;; ii++)
	{
		c = start[ii];
		if (c == 0)
		{
			set_error_simple (decoder, decoder->index,
			                  "Unterminated string.");
			return NULL;
		}
		
		/* Check for illegal characters */
		if (c < 0x20)
		{
			set_error_unexpected (decoder, start + ii, "printable characters");
			return NULL;
		}
		
		if (escaped)
		{
			/* Invalid escape codes will be caught
			 * later.
			**/
			escaped = FALSE;
		}
		
		else
		{	if (c == '\\')
			{
				fancy = TRUE;
				escaped = TRUE;
			}
			else if (c == '"') break;
		}
	}
	
	if (fancy)
	{
		return read_string_full (decoder, start, ii);
	}
	
	/* No fancy features, return the string directly */
	unicode = PyUnicode_FromUnicode (start, ii);
	if (unicode)
	{
		decoder->index = start + ii + 1;
	}
	return unicode;
}

static PyObject *
read_number (Decoder *decoder)
{
	PyObject *object = NULL;
	int is_float = FALSE, should_stop = FALSE, got_digit = FALSE,
	    leading_zero = FALSE, has_exponent = FALSE;
	Py_UNICODE *ptr, c;
	
	ptr = decoder->index;
	
	while ((c = *ptr))
	{
		switch (c) {
		case '0':
			if (!got_digit)
			{
				leading_zero = TRUE;
			}
			else if (leading_zero && !is_float)
			{
				set_error_simple (decoder, decoder->index,
				                  "Invalid number.");
				return NULL;
			}
			got_digit = TRUE;
			break;
		case '1':
		case '2':
		case '3':
		case '4':
		case '5':
		case '6':
		case '7':
		case '8':
		case '9':
			if (leading_zero && !is_float)
			{
				set_error_simple (decoder, decoder->index,
				                  "Invalid number.");
				return NULL;
			}
			got_digit = TRUE;
			break;
		case '-':
		case '+':
			break;
		case 'e':
		case 'E':
			has_exponent = TRUE;
			break;
		case '.':
			is_float = TRUE;
			got_digit = FALSE;
			break;
		default:
			should_stop = TRUE;
		}
		if (should_stop) {
			break;
		}
		ptr++;
	}
	
	if (got_digit)
	{
		if (is_float || has_exponent)
		{
			PyObject *unicode;
			if (!(unicode = PyUnicode_FromUnicode (decoder->index,
			                                       ptr - decoder->index)))
				return NULL;

            if (decoder->parse_float) {
                PyObject *args = PyTuple_Pack(1, unicode);
                object = PyObject_CallObject(decoder->parse_float, args);
                Py_DECREF(args);
            } else {
                object = PyFloat_FromString (unicode, NULL);
            }
			Py_DECREF (unicode);
		}
		
		else
		{
            if (decoder->parse_int) {
                PyObject *unicode;
                if (!(unicode = PyUnicode_FromUnicode (decoder->index,
                                                       ptr - decoder->index)))
                    return NULL;
                
                PyObject *args = PyTuple_Pack(1, unicode);
                Py_DECREF (unicode);
                
                object = PyObject_CallObject(decoder->parse_int, args);
                
                Py_DECREF(args);

            } else {                                             
                object = PyLong_FromUnicode (decoder->index,
                                             ptr - decoder->index, 10);
            }
		}
	}
	
	if (object == NULL)
	{
		set_error_simple (decoder, decoder->index, "Invalid number.");
		return NULL;
	}
	
	decoder->index = ptr;
	return object;
}

static int
read_array_impl (PyObject *list, Decoder *decoder)
{
	Py_UNICODE *start, c;
	ParseArrayState array_state = ARRAY_EMPTY;
	int next_atom;
	
	start = decoder->index;
	decoder->index++;
	while (TRUE)
	{
		skip_spaces (decoder);
		if (!(c = *decoder->index))
		{
			set_error_simple (decoder, start,
			                  "Unterminated array.");
			return FALSE;
		}
		
		switch (array_state)
		{
			case ARRAY_EMPTY:
				if (c == ']')
				{
					decoder->index++;
					return TRUE;
				}
			case ARRAY_NEED_VALUE:
				next_atom = parser_find_next_value (decoder);
				if (next_atom == 0)
				{
					PyObject *value;
					int result;
					
					if (!(value = json_read (decoder)))
						return FALSE;
					
					result  = PyList_Append (list, value);
					Py_DECREF (value);
					if (result == -1)
						return FALSE;
					
					array_state = ARRAY_GOT_VALUE;
					break;
				}
				
				set_error_unexpected (decoder, decoder->index, "object in array");
				return FALSE;
				
			case ARRAY_GOT_VALUE:
				if (c == ',')
				{
					array_state = ARRAY_NEED_VALUE;
					decoder->index++;
					break;
				}
				else if (c == ']')
				{
					decoder->index++;
					return TRUE;
				}
				set_error_unexpected (decoder, decoder->index, "comma");
				return FALSE;
		}
	}
}

static PyObject *
read_array (Decoder *decoder)
{
	PyObject *object = PyList_New (0);
	
	if (!read_array_impl (object, decoder))
	{
		Py_DECREF (object);
		return NULL;
	}
	
	return object;
}

static int
read_object_impl (PyObject *object, Decoder *decoder)
{
	Py_UNICODE *start, c;
	ParseObjectState object_state = OBJECT_EMPTY;
	PyObject *key = NULL;
	
	start = decoder->index;
	decoder->index++;
	while (TRUE)
	{
		skip_spaces (decoder);
		if (!(c = *decoder->index))
		{
			set_error_simple (decoder, start,
			                  "Unterminated object.");
			Py_XDECREF (key);
			return FALSE;
		}
		
		switch (object_state)
		{
			case OBJECT_EMPTY:
				if (c == '}')
				{
					decoder->index++;
					Py_XDECREF (key);
					return TRUE;
				}
			case OBJECT_NEED_KEY:
				assert (key == NULL);
				if (c != '"')
				{
					set_error_unexpected (decoder, decoder->index,
					                      "property name");
					return FALSE;
				}
				if (!(key = json_read (decoder)))
					return FALSE;
				object_state = OBJECT_NEED_COLON;
				break;
			case OBJECT_NEED_COLON:
				if (c != ':')
				{
					set_error_unexpected (decoder, decoder->index,
					                      "colon");
					Py_XDECREF (key);
					return FALSE;
				}
				decoder->index++;
				object_state = OBJECT_NEED_VALUE;
				break;
			case OBJECT_NEED_VALUE:
			{
				PyObject *value;
				int result, next_atom;
				
				assert (key != NULL);
				next_atom = parser_find_next_value (decoder);
				if (next_atom == 0)
				{
					if (!(value = json_read (decoder)))
					{
						Py_XDECREF (key);
						return FALSE;
					}
					result = PyDict_SetItem (object, key, value);
					Py_DECREF (key);
					Py_DECREF (value);
					key = NULL;
					if (result == -1)
						return FALSE;
					object_state = OBJECT_GOT_VALUE;
					break;
				}
				
				set_error_unexpected (decoder, decoder->index, "object in dictionary");
				return FALSE;
			}
			case OBJECT_GOT_VALUE:
				if (c == ',')
				{
					object_state = OBJECT_NEED_KEY;
					decoder->index++;
					break;
				}
				else if (c == '}')
				{
					decoder->index++;
					Py_XDECREF (key);
					return TRUE;
				}
				set_error_unexpected (decoder, decoder->index, "comma");
				Py_XDECREF (key);
				return FALSE;
		}
	}
}

static PyObject *
read_object (Decoder *decoder)
{
	PyObject *object = PyDict_New ();
	
	if (!read_object_impl (object, decoder))
	{
		Py_DECREF (object);
		return NULL;
	}
	
	return object;
}

static PyObject *
json_read (Decoder *decoder)
{
    PyObject *kw = NULL;
	skip_spaces (decoder);
	switch (*decoder->index)
	{
		case 0:
			set_error_simple (decoder, decoder->start,
			                  "No expression found.");
			return NULL;
		case '{':
			return read_object (decoder);
		case '[':
			return read_array (decoder);
		case '"':
			return read_string (decoder);
		case 't':
			if ((kw = keyword_compare (decoder, "true", 4, Py_True)))
				return kw;
			break;
		case 'f':
			if ((kw = keyword_compare (decoder, "false", 5, Py_False)))
				return kw;
			break;
		case 'n':
			if ((kw = keyword_compare (decoder, "null", 4, Py_None)))
				return kw;
			break;
        case 'N':
            if ((kw = keyword_compare (decoder, "NaN", 3, decoder->nan)))
                return kw;
            break;
        case 'I':
            if ((kw = keyword_compare (decoder, "Infinity", 8,
                                       decoder->infinity)))
                return kw;
            break;
            
		case '-':
            if ((kw = keyword_compare (decoder, "-Infinity", 9,
                                       decoder->neg_infinity)))
                return kw;
            /* fall through to number */
		case '0':
		case '1':
		case '2':
		case '3':
		case '4':
		case '5':
		case '6':
		case '7':
		case '8':
		case '9':
			return read_number (decoder);
		default:
			break;
	}
	set_error_unexpected (decoder, decoder->index, "<valid thing>");
	return NULL;
}

static int
detect_encoding (const char *const bytes, size_t size)
{
	/* 4 is the minimum size of a JSON expression encoded without UTF-8. */
	if (size < 4) { return UTF_8; }
	
	if (memcmp (bytes, BOM_UTF8, 3) == 0) return UTF_8_BOM;
	if (memcmp (bytes, BOM_UTF32_LE, 4) == 0) return UTF_32_LE_BOM;
	if (memcmp (bytes, BOM_UTF32_BE, 4) == 0) return UTF_32_BE_BOM;
	if (memcmp (bytes, BOM_UTF16_LE, 2) == 0) return UTF_16_LE_BOM;
	if (memcmp (bytes, BOM_UTF16_BE, 2) == 0) return UTF_16_BE_BOM;
	
	/* No BOM found. Examine the byte patterns of the first four
	 * characters.
	**/
	if (bytes[0] && !bytes[1] && bytes[2] && !bytes[3])
		return UTF_16_LE;
	
	if (!bytes[0] && bytes[1] && !bytes[2] && bytes[3])
		return UTF_16_BE;
	
	if (bytes[0] && !bytes[1] && !bytes[2] && !bytes[3])
		return UTF_32_LE;
	
	if (!bytes[0] && !bytes[1] && !bytes[2] && bytes[3])
		return UTF_32_BE;
	
	/* Default to UTF-8. */
	return UTF_8;
}

/**
 * Intelligently convert a byte string to Unicode.
 * 
 * Assumes the encoding used is one of the UTF-* variants. If the
 * input is already in unicode, this is a noop.
**/
static PyObject *
unicode_autodetect (PyObject *bytestring)
{
	PyObject *u = NULL;
	char *bytes;
	size_t byte_count;
	
	bytes = PyString_AS_STRING (bytestring);
	byte_count = PyString_GET_SIZE (bytestring);
	switch (detect_encoding (bytes, byte_count))
	{
	case UTF_8:
		u = PyUnicode_Decode (bytes, byte_count, "utf-8", "strict");
		break;
	case UTF_8_BOM:
		/* 3 = sizeof UTF-8 BOM */
		u = PyUnicode_Decode (bytes + 3, byte_count - 3, "utf-8", "strict");
		break;
	case UTF_16_LE:
		u = PyUnicode_Decode (bytes, byte_count, "utf-16-le", "strict");
		break;
	case UTF_16_LE_BOM:
		u = PyUnicode_Decode (bytes + 2, byte_count - 2, "utf-16-le", "strict");
		break;
	case UTF_16_BE:
		u = PyUnicode_Decode (bytes, byte_count, "utf-16-be", "strict");
		break;
	case UTF_16_BE_BOM:
		u = PyUnicode_Decode (bytes + 2, byte_count - 2, "utf-16-be", "strict");
		break;
	case UTF_32_LE:
		u = PyUnicode_Decode (bytes, byte_count, "utf-32-le", "strict");
		break;
	case UTF_32_LE_BOM:
		u = PyUnicode_Decode (bytes + 4, byte_count - 4, "utf-32-le", "strict");
		break;
	case UTF_32_BE:
		u = PyUnicode_Decode (bytes, byte_count, "utf-32-be", "strict");
		break;
	case UTF_32_BE_BOM:
		u = PyUnicode_Decode (bytes + 4, byte_count - 4, "utf-32-be", "strict");
		break;
	}
	return u;
}

/* Parses the argument list to _read(), automatically converting from
 * a UTF-* encoded bytestring to unicode if needed.
**/
static int
parse_unicode_arg (Decoder *decoder,
                   PyObject *args, PyObject *kwargs, PyObject **unicode)
{
	int retval;
	PyObject *bytestring;
    
	static char *kwlist[] = {"string",
                             "parse_float", "parse_int", "parse_constant",
                             NULL};
	
	/* Try for the common case of a direct unicode string. */
	retval = PyArg_ParseTupleAndKeywords (args, kwargs, "U|OOO:read",
	                                      kwlist, unicode,
                                          &decoder->parse_float,
                                          &decoder->parse_int,
                                          &decoder->parse_constant);
	if (retval)
	{
		Py_INCREF (*unicode);
		return retval;
	}

    /* clear the parse exception from before, because we want the next
       one to throw the error, not this one */
	PyErr_Clear ();
	/* Might have been passed a string. Try to autodecode it. */
	retval = PyArg_ParseTupleAndKeywords (args, kwargs, "S|OOO:read",
	                                      kwlist, &bytestring,
                                          &decoder->parse_float,
                                          &decoder->parse_int,
                                          &decoder->parse_constant);
	if (!retval)
	{
        /* success! */
		return retval;
	}
	
	*unicode = unicode_autodetect (bytestring);
	if (!(*unicode)) return 0;
	return 1;
}

static PyObject*
_read_entry (PyObject *self, PyObject *args, PyObject *kwargs)
{
	PyObject *result = NULL, *unicode;
	Decoder decoder = { NULL };
    decoder.infinity = PyFloat_FromDouble(Py_HUGE_VAL);
    decoder.neg_infinity = PyFloat_FromDouble(-Py_HUGE_VAL);
    decoder.nan = PyFloat_FromDouble(Py_NAN);
    decoder.parse_float = decoder.parse_int = decoder.parse_constant = NULL;
	
	if (!parse_unicode_arg (&decoder, args, kwargs, &unicode))
		return NULL;
	
	decoder.start = PyUnicode_AsUnicode (unicode);
	decoder.end = decoder.start + PyUnicode_GetSize (unicode);
	decoder.index = decoder.start;
	
    result = json_read (&decoder);
	
	if (result)
	{
		skip_spaces (&decoder);
		if (decoder.index < decoder.end)
		{
			set_error_simple (&decoder, decoder.index,
			                  "Extra data after JSON expression.");
			Py_DECREF (result);
			result = NULL;
		}
	}
	Py_DECREF (unicode);
	
	if (decoder.stringparse_buffer)
		PyMem_Free (decoder.stringparse_buffer);

    Py_XDECREF(decoder.infinity);
    Py_XDECREF(decoder.neg_infinity);
    Py_XDECREF(decoder.nan);
    Py_XDECREF(decoder.parse_float);
    Py_XDECREF(decoder.parse_int);
    Py_XDECREF(decoder.parse_constant);
	
	return result;
}
/* }}} */

/* serializer {{{ */
static int
buffer_encoder_append_ascii (Encoder *base_encoder,
                             const char *text,
                             const size_t len)
{
	BufferEncoder *encoder = (BufferEncoder *) (base_encoder);
	size_t ii;
	
	if (!buffer_encoder_resize (encoder, len))
		return FALSE;
	for (ii = 0; ii < len; ii++)
	{
		encoder->buffer[encoder->buffer_size++] = text[ii];
	}
	return TRUE;
}

static int
buffer_encoder_append_unicode (Encoder *base_encoder,
                               PyObject *text)
{
	size_t len;
	Py_UNICODE *raw;
	BufferEncoder *encoder = (BufferEncoder *) (base_encoder);
	
	raw = PyUnicode_AS_UNICODE (text);
	len = PyUnicode_GET_SIZE (text);
	
	if (!buffer_encoder_resize (encoder, len))
		return FALSE;
	memcpy (encoder->buffer + encoder->buffer_size, raw,
	        len * sizeof (Py_UNICODE));
	encoder->buffer_size += len;
	return TRUE;
}

static int
stream_encoder_append_common (StreamEncoder *encoder, PyObject *encoded)
{
	int result;
	if (!encoded)
		return FALSE;
	result = PyFile_WriteObject (encoded, encoder->stream, Py_PRINT_RAW);
	Py_DECREF (encoded);
	return (result == 0);
}

static int
stream_encoder_append_ascii (Encoder *base_encoder,
                             const char *text,
                             const size_t len)
{
	StreamEncoder *encoder = (StreamEncoder *) (base_encoder);
	PyObject *encoded;
	if (encoder->encoding)
		encoded = PyString_Encode (text, len, encoder->encoding, "strict");
	else
		encoded = PyUnicode_Decode (text, len, "ascii", "strict");
	return stream_encoder_append_common (encoder, encoded);
}

static int
stream_encoder_append_unicode (Encoder *base_encoder,
                               PyObject *text)
{
	StreamEncoder *encoder = (StreamEncoder *) (base_encoder);
	PyObject *encoded;
	if (encoder->encoding)
		encoded = PyUnicode_AsEncodedString (text, encoder->encoding, "strict");
	else
	{
		encoded = text;
		Py_INCREF (encoded);
	}
	return stream_encoder_append_common (encoder, encoded);
}

static int
encoder_append_string (Encoder *encoder, PyObject *text)
{
	size_t len;
	
	if (PyUnicode_CheckExact (text))
	{
		return encoder->append_unicode (encoder, text);
	}
	if (PyString_CheckExact (text))
	{
		char *raw = PyString_AS_STRING (text);
		len = PyString_GET_SIZE (text);
		return encoder->append_ascii (encoder, raw, len);
	}
	
	PyErr_SetString (PyExc_AssertionError, "type (text) in (str, unicode)");
	return FALSE;
}

static int
buffer_encoder_resize (BufferEncoder *encoder, size_t delta)
{
	size_t new_size;
	Py_UNICODE *new_buf;
	
	new_size = encoder->buffer_size + delta;
	if (encoder->buffer_max_size >= new_size)
		return TRUE;
		
	if (!encoder->buffer)
	{
		new_size = (delta > INITIAL_BUFFER_SIZE? delta : INITIAL_BUFFER_SIZE);
		new_size = next_power_2 (1, new_size);
		encoder->buffer = PyMem_Malloc (sizeof (Py_UNICODE) * new_size);
		encoder->buffer_max_size = new_size;
		return TRUE;
	}
	
	new_size = next_power_2 (encoder->buffer_max_size, new_size);
	new_buf = PyMem_Realloc (encoder->buffer,
	                         sizeof (Py_UNICODE) * new_size);
	if (!new_buf)
	{
		PyMem_Free (encoder->buffer);
		return FALSE;
	}
	encoder->buffer = new_buf;
	encoder->buffer_max_size = new_size;
	return TRUE;
}

static void
set_unknown_serializer (PyObject *value)
{
	PyObject *message;
	
	message = jsonlib_str_format ("No known serializer for object: %r",
	                              Py_BuildValue ("(O)", value));
	if (message)
	{
		PyErr_SetObject (UnknownSerializerError, message);
		Py_DECREF (message);
	}
}

static PyObject *
ascii_constant (const char *value, int len)
{
	if (len < 0)
		len = strlen (value);
	return PyUnicode_DecodeASCII (value, len, "strict");
}

static PyObject *
unicode_from_format (const char *format, ...)
{
	PyObject *retval, *string;
	va_list args;
	
	va_start (args, format);
	string = PyString_FromFormatV (format, args);
	va_end (args);
	
	if (!string) return NULL;
	retval = PyUnicode_FromObject (string);
	Py_DECREF (string);
	return retval;
}

static void
get_separators (PyObject *indent_string, int indent_level,
                PyObject *comma,
                char start, char end,
                PyObject **start_ptr, PyObject **end_ptr,
                PyObject **pre_value_ptr, PyObject **post_value_ptr)
{
	if (indent_string == Py_None)
	{
		(*start_ptr) = ascii_constant (&start, 1);
		(*pre_value_ptr) = NULL;
		(*post_value_ptr) = comma;
        Py_INCREF(*post_value_ptr);
		(*end_ptr) = ascii_constant (&end, 1);
	}
	else
	{
		PyObject *format_args, *format_tmpl, *indent, *next_indent;
		char start_str[] = {0, '\n'};
		start_str[0] = start;
		
		(*start_ptr) = ascii_constant (start_str, 2);
        /* XXX: need to handle 'comma' string here with %s\n */
		(*post_value_ptr) = ascii_constant (",\n", 2);
		
		indent = PySequence_Repeat (indent_string, indent_level + 1);
		(*pre_value_ptr) = indent;
		
		next_indent = PySequence_Repeat (indent_string, indent_level);
		format_args = Py_BuildValue ("(N)", next_indent);
		format_tmpl = unicode_from_format ("\n%%s%c", end);
		(*end_ptr) = PyUnicode_Format (format_tmpl, format_args);
		Py_DECREF (format_args);
		Py_DECREF (format_tmpl);
	}
}

static PyObject *
write_string (Encoder *encoder, PyObject *string)
{
	PyObject *exc_type, *exc_value, *exc_traceback;
	PyObject *unicode, *retval;
	int safe = TRUE;
    int escape_slash = encoder->escape_slash;
	char *buffer;
	size_t ii;
	Py_ssize_t str_len;
	
	/* Scan the string for non-ASCII values. If none exist, the string
	 * can be returned directly (with quotes).
	**/
	if (PyString_AsStringAndSize (string, &buffer, &str_len) == -1)
		return NULL;

	for (ii = 0; ii < (size_t)str_len; ++ii)
	{
		if (buffer[ii] == '"' ||
		    (escape_slash && buffer[ii] == '/') ||
		    buffer[ii] == '\\' ||
		    buffer[ii] < 0x20 ||
		    buffer[ii] > 0x7E)
		{
			safe = FALSE;
			break;
		}
	}
	
	if (safe)
	{
		return PyString_FromFormat ("\"%s\"", buffer);
	}
	
	/* Convert to Unicode and run through the escaping
	 * mechanism.
	**/
	Py_INCREF (string);
	PyErr_Fetch (&exc_type, &exc_value, &exc_traceback);
	unicode = PyString_AsDecodedObject (string, "ascii", "strict");
	PyErr_Restore (exc_type, exc_value, exc_traceback);
	if (!unicode) {
        unicode = unicode_autodetect(string);
        if (!unicode) {
            Py_DECREF (string);
            return NULL;
        }
	}
	PyErr_Clear ();
	Py_DECREF (string);
    
	if (encoder->ensure_ascii)
		retval = unicode_to_ascii (unicode, escape_slash);
	else
		retval = unicode_to_unicode (unicode, escape_slash);
	Py_DECREF (unicode);
	return retval;
}

static PyObject *
unicode_to_unicode (PyObject *unicode, int escape_slash)
{
	PyObject *retval;
	Py_UNICODE *old_buffer, *p, c;
	size_t ii, old_buffer_size, new_buffer_size;
	
	old_buffer = PyUnicode_AS_UNICODE (unicode);
	old_buffer_size = PyUnicode_GET_SIZE (unicode);
	
	/*
	Calculate the size needed to store the final string:
	
		* 2 chars for opening and closing quotes
		* 2 chars each for each of these characters:
			* U+0008
			* U+0009
			* U+000A
			* U+000C
			* U+000D
			* U+0022
			* U+002F
			* U+005C
		* 6 chars for other characters <= U+001F
		* 1 char for other characters.
	
	*/
	new_buffer_size = 2;
	for (ii = 0; ii < old_buffer_size; ii++)
	{
		c = old_buffer[ii];
		if (c == 0x08 ||
		    c == 0x09 ||
		    c == 0x0A ||
		    c == 0x0C ||
		    c == 0x0D ||
		    c == 0x22 ||
		    (escape_slash && c == 0x2F) ||
		    c == 0x5C)
			new_buffer_size += 2;
		else if (c <= 0x1F)
			new_buffer_size += 6;
		else
			new_buffer_size += 1;
	}
	
	retval = PyUnicode_FromUnicode (NULL, new_buffer_size);
	if (!retval) return NULL;
	
	/* Fill the new buffer */
	p = PyUnicode_AS_UNICODE (retval);
	*p++ = '"';
	for (ii = 0; ii < old_buffer_size; ii++)
	{
		c = old_buffer[ii];
		if (c == 0x08)
			*p++ = '\\', *p++ = 'b';
		else if (c == 0x09)
			*p++ = '\\', *p++ = 't';
		else if (c == 0x0A)
			*p++ = '\\', *p++ = 'n';
		else if (c == 0x0C)
			*p++ = '\\', *p++ = 'f';
		else if (c == 0x0D)
			*p++ = '\\', *p++ = 'r';
		else if (c == 0x22)
			*p++ = '\\', *p++ = '"';
		else if (escape_slash && c == 0x2F)
			*p++ = '\\', *p++ = '/';
		else if (c == 0x5C)
			*p++ = '\\', *p++ = '\\';
		else if (c <= 0x1F)
		{
			*p++ = '\\';
			*p++ = 'u';
			*p++ = '0';
			*p++ = '0';
			*p++ = hexdigit[(c >> 4) & 0x0000000F];
			*p++ = hexdigit[c & 0x0000000F];
		}
		else
			*p++ = c;
	}
	*p++ = '"';
	return retval;
}

static char *
escape_unichar (Py_UNICODE c, char *p)
{
	*p++ = '\\';
	switch (c)
	{
		case 0x08: *p++ = 'b'; return p;
		case 0x09: *p++ = 't'; return p;
		case 0x0A: *p++ = 'n'; return p;
		case 0x0C: *p++ = 'f'; return p;
		case 0x0D: *p++ = 'r'; return p;
		case 0x22: *p++ = '"'; return p;
        case 0x2F: *p++ = '/'; return p;
		case 0x5C: *p++ = '\\'; return p;
		default: break;
	}
#ifdef Py_UNICODE_WIDE
	if (c > 0xFFFF)
	{
		/* Separate into upper and lower surrogate pair */
		Py_UNICODE reduced, upper, lower;
		
		reduced = c - 0x10000;
		lower = (reduced & 0x3FF);
		upper = (reduced >> 10);
		
		upper += 0xD800;
		lower += 0xDC00;
		
		*p++ = 'u';
		*p++ = hexdigit[(upper >> 12) & 0x0000000F];
		*p++ = hexdigit[(upper >> 8) & 0x0000000F];
		*p++ = hexdigit[(upper >> 4) & 0x0000000F];
		*p++ = hexdigit[upper & 0x0000000F];
		
		*p++ = '\\';
		*p++ = 'u';
		*p++ = hexdigit[(lower >> 12) & 0x0000000F];
		*p++ = hexdigit[(lower >> 8) & 0x0000000F];
		*p++ = hexdigit[(lower >> 4) & 0x0000000F];
		*p++ = hexdigit[lower & 0x0000000F];
		return p;
	}
#endif
	*p++ = 'u';
	*p++ = hexdigit[(c >> 12) & 0x000F];
	*p++ = hexdigit[(c >> 8) & 0x000F];
	*p++ = hexdigit[(c >> 4) & 0x000F];
	*p++ = hexdigit[c & 0x000F];
	return p;
}

static PyObject *
unicode_to_ascii (PyObject *unicode, int escape_slash)
{
	PyObject *retval;
	Py_UNICODE *old_buffer;
	char *p;
	size_t ii, old_buffer_size, new_buffer_size;
	
	old_buffer = PyUnicode_AS_UNICODE (unicode);
	old_buffer_size = PyUnicode_GET_SIZE (unicode);
	
	/*
	Calculate the size needed to store the final string:
	
		* 2 chars for opening and closing quotes
		* 2 chars each for each of these characters:
			* U+0008
			* U+0009
			* U+000A
			* U+000C
			* U+000D
			* U+0022
			* U+002F
			* U+005C
		* 6 chars for other characters <= U+001F
		* 12 chars for characters > 0xFFFF
		* 6 chars for characters > 0x7E
		* 1 char for other characters.
	
	*/
	new_buffer_size = 2;
	for (ii = 0; ii < old_buffer_size; ii++)
	{
		Py_UNICODE c = old_buffer[ii];
		if (c == 0x08 ||
		    c == 0x09 ||
		    c == 0x0A ||
		    c == 0x0C ||
		    c == 0x0D ||
		    c == 0x22 ||
		    (escape_slash && c == 0x2F) ||
		    c == 0x5C)
			new_buffer_size += 2;
		else if (c <= 0x1F)
			new_buffer_size += 6;
			
#		ifdef Py_UNICODE_WIDE
			else if (c > 0xFFFF)
				new_buffer_size += 12;
#		endif
		
		else if (c > 0x7E)
			new_buffer_size += 6;
		else
			new_buffer_size += 1;
	}
	
	retval = PyString_FromStringAndSize (NULL, new_buffer_size);
	if (!retval) return NULL;
	
	/* Fill the new buffer */
	p = PyString_AS_STRING (retval);
	*p++ = '"';
	for (ii = 0; ii < old_buffer_size; ii++)
	{
		Py_UNICODE c = old_buffer[ii];
		if (c > 0x1F && c <= 0x7E &&
            c != '\\' &&
            c != '"' &&
            (!escape_slash || c != '/'))
			*p++ = (char) (c);
		else
			p = escape_unichar (c, p);
	}
	*p++ = '"';
	return retval;
}

static PyObject *
write_unicode (Encoder *encoder, PyObject *unicode)
{
	PyObject *retval;
	int safe = TRUE;
	Py_UNICODE *buffer;
    int escape_slash = encoder->escape_slash;
	size_t ii, str_len;
	
	/* Check if the string can be returned directly */
	buffer = PyUnicode_AS_UNICODE (unicode);
	str_len = PyUnicode_GET_SIZE (unicode);
	
	for (ii = 0; ii < str_len; ++ii)
	{
		if (buffer[ii] == '"' ||
		    (escape_slash && buffer[ii] == '/') ||
		    buffer[ii] == '\\' ||
		    buffer[ii] < 0x20 ||
		    (encoder->ensure_ascii && buffer[ii] > 0x7E))
		{
			safe = FALSE;
			break;
		}
	}
	
	if (safe)
	{
		PyUnicodeObject *u_retval;
		
		if (!(retval = PyUnicode_FromUnicode (NULL, str_len + 2)))
			return NULL;
			
		u_retval = (PyUnicodeObject*) retval;
		Py_UNICODE_COPY (u_retval->str + 1, buffer, str_len);
		u_retval->str[0] = '"';
		u_retval->str[str_len + 1] = '"';
		
		return retval;
	}
	
	/* Scan through again to check for invalid surrogate pairs */
	for (ii = 0; ii < str_len; ++ii)
	{
		if (0xD800 <= buffer[ii] && buffer[ii] <= 0xDBFF)
		{
			if (++ii == str_len)
			{
				PyErr_SetString (WriteError,
				                 "Cannot serialize incomplete"
						 " surrogate pair.");
				return NULL;
			}
			else if (!(0xDC00 <= buffer[ii] && buffer[ii] <= 0xDFFF))
			{
				PyErr_SetString (WriteError,
				                 "Cannot serialize invalid surrogate pair.");
				return NULL;
			}
		}
		else if (0xDC00 <= buffer[ii] && buffer[ii] <= 0xDFFF)
		{
			PyObject *err_msg;
			
			err_msg = jsonlib_str_format ("Cannot serialize reserved code point U+%04X.",
			                              Py_BuildValue ("(k)", buffer[ii]));
			if (err_msg)
			{
				PyErr_SetObject (WriteError, err_msg);
				Py_DECREF (err_msg);
			}
			return NULL;
		}
	}
	
	if (encoder->ensure_ascii)
		return unicode_to_ascii (unicode, escape_slash);
	return unicode_to_unicode (unicode, escape_slash);
}

static int
write_sequence_impl (Encoder *encoder, PyObject *seq,
                     PyObject *start, PyObject *end,
                     PyObject *pre_value, PyObject *post_value,
                     int indent_level)
{
	Py_ssize_t ii;
	
	if (!encoder_append_string (encoder, start))
		return FALSE;
	
	/* Check size every loop because the sequence might be mutable */
	for (ii = 0; ii < PySequence_Fast_GET_SIZE (seq); ++ii)
	{
		PyObject *item;
		
		if (pre_value && !encoder_append_string (encoder, pre_value))
			return FALSE;
		
		if (!(item = PySequence_Fast_GET_ITEM (seq, ii)))
			return FALSE;
		
		if (!write_object (encoder, item, indent_level + 1, FALSE))
			return FALSE;
		
		if (ii + 1 < PySequence_Fast_GET_SIZE (seq))
		{
			if (!encoder_append_string (encoder, post_value))
				return FALSE;
		}
	}
	
	return encoder_append_string (encoder, end);
}

static int
write_iterable (Encoder *encoder, PyObject *iter, int indent_level)
{
	PyObject *sequence;
	PyObject *start, *end, *pre, *post;
	int has_parents, succeeded;
	
	/* Guard against infinite recursion */
	has_parents = Py_ReprEnter (iter);
	if (has_parents > 0)
	{
		PyErr_SetString (WriteError,
		                 "Cannot serialize self-referential"
		                 " values.");
	}
	if (has_parents != 0) return FALSE;
	
	sequence = PySequence_Fast (iter, "Error converting iterable to sequence.");
	
	/* Shortcut for len (sequence) == 0 */
	if (PySequence_Fast_GET_SIZE (sequence) == 0)
	{
		Py_DECREF (sequence);
		Py_ReprLeave (iter);
		return encoder->append_ascii (encoder, "[]", 2);
	}
	
	/* Build separator strings */
	get_separators (encoder->indent_string, indent_level,
                    encoder->comma, '[', ']',
	                &start, &end, &pre, &post);
	
	succeeded = write_sequence_impl (encoder, sequence,
	                                 start, end, pre, post,
	                                 indent_level);
	
	Py_DECREF (sequence);
	Py_ReprLeave (iter);
	
	Py_XDECREF (start);
	Py_XDECREF (end);
	Py_XDECREF (pre);
	Py_XDECREF (post);
	return succeeded;
}

static int
mapping_process_key (Encoder *encoder, PyObject *key, PyObject **key_ptr)
{
	(*key_ptr) = NULL;
	
	if (PyString_Check (key) || PyUnicode_Check (key))
	{
		Py_INCREF (key);
		*key_ptr = key;
		return TRUE;
	}
	
	if (PyObject_IsInstance (key, encoder->UserString))
	{
		Py_INCREF (key);
		*key_ptr = PyObject_Str (key);
		Py_DECREF (key);
		if (*key_ptr) return TRUE;
		return FALSE;
	}

	if (encoder->coerce_keys)
	{
		PyObject *new_key = NULL;
		Py_INCREF (key);
		if (!(new_key = write_basic (encoder, key)))
		{
			if (PyErr_ExceptionMatches (UnknownSerializerError))
			{
				PyErr_Clear ();
				new_key = PyObject_Unicode (key);
			}
		}
		Py_DECREF (key);
		
		if (!new_key) return FALSE;
		*key_ptr = new_key;
		return TRUE;
	}
	PyErr_Format(WriteError,
                    "Only strings may be used as object keys, not %r",
                    key);
	return FALSE;
}

static int
mapping_get_key_and_value_from_item (Encoder *encoder, PyObject *item,
                                     PyObject **key_ptr, PyObject **value_ptr)
{
	PyObject *key = NULL, *value = NULL;
	int retval;
	
	(*key_ptr) = NULL;
	(*value_ptr) = NULL;
	
	key = PySequence_GetItem (item, 0);
	value = PySequence_GetItem (item, 1);
	
	if (!(key && value))
	{
		Py_XDECREF (key);
		Py_XDECREF (value);
		return FALSE;
	}
	
	if ((retval = mapping_process_key (encoder, key, key_ptr)))
	{
		*value_ptr = value;
	}
	return retval;
}

/* Special case for dictionaries */
static int
write_dict (Encoder *encoder, PyObject *dict, PyObject *start,
            PyObject *end, PyObject *pre_value, PyObject *post_value,
            int indent_level)
{
	size_t ii = 0, item_count;
	Py_ssize_t dict_pos = 0;
	PyObject *raw_key, *value;
	int status;
	
	if (!encoder_append_string (encoder, start))
		return FALSE;
	
	item_count = PyDict_Size (dict);
	while (PyDict_Next (dict, &dict_pos, &raw_key, &value))
	{
		PyObject *serialized, *key;
		
		if (pre_value && !encoder_append_string (encoder, pre_value))
			return FALSE;
		
		if (!mapping_process_key (encoder, raw_key, &key))
			return FALSE;
		
		serialized = write_basic (encoder, key);
		Py_DECREF (key);
		if (!serialized)
			return FALSE;
		
		status = encoder_append_string (encoder, serialized);
		Py_DECREF (serialized);
		if (!status)
			return FALSE;
		
		if (!encoder_append_string (encoder, encoder->colon))
			return FALSE;
		
		if (!write_object (encoder, value, indent_level + 1, FALSE))
			return FALSE;
		
		if (ii + 1 < item_count)
		{
			if (!encoder_append_string (encoder, post_value))
			{
				return FALSE;
			}
		}
		ii++;
	}
	
	return encoder_append_string (encoder, end);
}

static int
write_mapping_impl (Encoder *encoder, PyObject *items,
                    PyObject *start, PyObject *end, PyObject *pre_value,
                    PyObject *post_value, int indent_level)
{
	int status;
	size_t ii, item_count;
	
	if (!encoder_append_string (encoder, start))
		return FALSE;
	
	item_count = PySequence_Size (items);
	for (ii = 0; ii < item_count; ++ii)
	{
		PyObject *item, *key, *value, *serialized;
		
		if (pre_value && !encoder_append_string (encoder, pre_value))
			return FALSE;
		
		if (!(item = PySequence_GetItem (items, ii)))
			return FALSE;
		
		status = mapping_get_key_and_value_from_item (encoder, item, &key, &value);
		Py_DECREF (item);
		if (!status) return FALSE;
		
		serialized = write_basic (encoder, key);
		Py_DECREF (key);
		if (!serialized)
		{
			Py_DECREF (value);
			return FALSE;
		}
		
		status = encoder_append_string (encoder, serialized);
		Py_DECREF (serialized);
		if (!status)
		{
			Py_DECREF (value);
			return FALSE;
		}
		
		if (!encoder_append_string (encoder, encoder->colon))
		{
			Py_DECREF (value);
			return FALSE;
		}
		
		status = write_object (encoder, value, indent_level + 1, FALSE);
		Py_DECREF (value);
		if (!status)
			return FALSE;
		
		if (ii + 1 < item_count)
		{
			if (!encoder_append_string (encoder, post_value))
			{
				return FALSE;
			}
		}
	}
	
	return encoder_append_string (encoder, end);
}

static int
write_mapping (Encoder *encoder, PyObject *mapping, int indent_level)
{
	int has_parents, succeeded;
	PyObject *items;
	PyObject *start, *end, *pre_value, *post_value;
	
	if (PyMapping_Size (mapping) == 0)
		return encoder->append_ascii (encoder, "{}", 2);
	
	has_parents = Py_ReprEnter (mapping);
	if (has_parents != 0)
	{
		if (has_parents > 0)
		{
			PyErr_SetString (WriteError,
			                 "Cannot serialize self-referential"
			                 " values.");
		}
		return FALSE;
	}
	
	get_separators (encoder->indent_string, indent_level,
                    encoder->comma, '{', '}',
	                &start, &end, &pre_value, &post_value);
	
	Py_INCREF (mapping);
	if (PyDict_CheckExact (mapping) && !encoder->sort_keys)
		succeeded = write_dict (encoder, mapping, start, end,
		                        pre_value, post_value,
		                        indent_level);
	
	else
	{
		if (!(items = PyMapping_Items (mapping)))
		{
			Py_ReprLeave (mapping);
			Py_DECREF (mapping);
			return FALSE;
		}
		if (encoder->sort_keys) PyList_Sort (items);
		
		
		succeeded = write_mapping_impl (encoder, items, start, end,
		                                pre_value, post_value,
		                                indent_level);
		Py_DECREF (items);
	}
	
	Py_ReprLeave (mapping);
	Py_DECREF (mapping);
	Py_XDECREF (start);
	Py_XDECREF (end);
	Py_XDECREF (pre_value);
	Py_XDECREF (post_value);
	
	return succeeded;
}

static PyObject *
write_float (Encoder *encoder, PyObject *value)
{
	double val = PyFloat_AS_DOUBLE (value);
	if (Py_IS_NAN (val))
	{
        if (encoder->allow_nan) {
            Py_INCREF(encoder->nan_str);
            return encoder->nan_str;
        }
        
        PyErr_SetString (WriteError,
                         "Cannot serialize NaN.");
        return NULL;
	}
	
	if (Py_IS_INFINITY (val))
	{
        if (encoder->allow_nan) {
            if (val > 0) {
                Py_INCREF(encoder->inf_str);
                return encoder->inf_str;
            } else {
                Py_INCREF(encoder->neg_inf_str);
                return encoder->neg_inf_str;
            }
        }
        
		const char *msg;
		if (val > 0)
			msg = "Cannot serialize Infinity.";
		else
			msg = "Cannot serialize -Infinity.";
		
		PyErr_SetString (WriteError, msg);
		return NULL;
	}
	
	return PyObject_Repr (value);
}

static PyObject *
write_basic (Encoder *encoder, PyObject *value)
{
	if (value == Py_True)
	{
		Py_INCREF (encoder->true_str);
		return encoder->true_str;
	}
	if (value == Py_False)
	{
		Py_INCREF (encoder->false_str);
		return encoder->false_str;
	}
	if (value == Py_None)
	{
		Py_INCREF (encoder->null_str);
		return encoder->null_str;
	}
	
	/* Fast, exact type checks */
	if (PyString_CheckExact (value))
		return write_string (encoder, value);
	if (PyUnicode_CheckExact (value))
		return write_unicode (encoder, value);
	if (PyInt_CheckExact (value) || PyLong_CheckExact (value))
		return PyObject_Str (value);
	if (PyFloat_CheckExact (value))
		return write_float (encoder, value);
	
	/* Slow, full type checks */
	if (PyString_Check (value))
		return write_string (encoder, value);
	if (PyUnicode_Check (value))
		return write_unicode (encoder, value);
	if (PyInt_Check (value) || PyLong_Check (value))
		return PyObject_Str (value);
	if (PyFloat_Check (value))
		return write_float (encoder, value);
	
	if (PyComplex_Check (value))
	{
		Py_complex complex = PyComplex_AsCComplex (value);
		if (complex.imag == 0)
		{
			PyObject *real, *serialized;
			if (!(real = PyFloat_FromDouble (complex.real)))
				return NULL;
			serialized = PyObject_Repr (real);
			Py_DECREF (real);
			return serialized;
		}
		PyErr_SetString (WriteError,
		                 "Cannot serialize complex numbers with"
		                 " imaginary components.");
		return NULL;
	}
	
	if (PyObject_IsInstance (value, encoder->UserString))
	{
		PyObject *as_string, *retval;
		Py_INCREF (value);
		as_string = PyObject_Str (value);
		Py_DECREF (value);
		if (!as_string)
			return NULL;
		retval = write_string (encoder, as_string);
		Py_DECREF (as_string);
		return retval;
	}

	set_unknown_serializer (value);
	return NULL;
}

static int
write_object (Encoder *encoder, PyObject *object,
              int indent_level, int in_unknown_hook)
{
	PyObject *pieces, *iter, *default_args;
	PyObject *exc_type, *exc_value, *exc_traceback;
	
	if (PyList_Check (object) || PyTuple_Check (object))
	{
		return write_iterable (encoder, object, indent_level);
	}
	
	else if (PyDict_Check (object))
	{
		return write_mapping (encoder, object, indent_level);
	}
	
	if ((pieces = write_basic (encoder, object)))
	{
		int retval = FALSE;
		retval = encoder_append_string (encoder, pieces);
		Py_DECREF (pieces);
		return retval;
	}
	
	if (!PyErr_ExceptionMatches (UnknownSerializerError))
		return FALSE;
	
	if (PyObject_HasAttrString (object, "items"))
	{
		PyErr_Clear ();
		return write_mapping (encoder, object, indent_level);
	}
	
	if (PySequence_Check (object))
	{
		PyErr_Clear ();
		return write_iterable (encoder, object, indent_level);
	}

    /* try calling iter(object) to see if its iterable */
    
	PyErr_Fetch (&exc_type, &exc_value, &exc_traceback);
	iter = PyObject_GetIter (object);
	PyErr_Restore (exc_type, exc_value, exc_traceback);
	if (iter)
	{
		int retval;
		PyErr_Clear ();
		retval = write_iterable (encoder, iter, indent_level);
		Py_DECREF (iter);
		return retval;
	}
    
	PyErr_Clear ();
	if (encoder->default_handler == Py_None || in_unknown_hook)
	{
		set_unknown_serializer (object);
		return FALSE;
	}
	
	/* Call the `default` hook */
	if (!(default_args = PyTuple_Pack (1, object)))
		return FALSE;
	
	object = PyObject_CallObject (encoder->default_handler, default_args);
	Py_DECREF (default_args);
	if (object)
		return write_object (encoder, object, indent_level, TRUE);
	
	return FALSE;
}

static int
valid_json_whitespace (PyObject *string)
{
	char *c_str;
	Py_ssize_t c_str_len;
	size_t ii;
	
	if (string == Py_None) return TRUE;
	if (PyString_AsStringAndSize (string, &c_str, &c_str_len) == -1)
		return FALSE;
	for (ii = 0; ii < (size_t)c_str_len; ii++)
	{
		char c = c_str[ii];
		if (!(c == '\x09' ||
		      c == '\x0A' ||
		      c == '\x0D' ||
		      c == '\x20'))
			return FALSE;
	}
	return TRUE;
}

static int
serializer_init_and_run_common (Encoder *encoder, PyObject *value)
{
	int indent_is_valid, succeeded = FALSE;
	
	if (!(encoder->default_handler == Py_None ||
	      PyCallable_Check (encoder->default_handler)))
	{
		PyErr_SetString (PyExc_TypeError,
		                 "The 'default' object must be callable.");
		return FALSE;
	}
	
	indent_is_valid = valid_json_whitespace (encoder->indent_string);
	if (!indent_is_valid)
	{
		if (indent_is_valid > -1)
			PyErr_SetString (PyExc_TypeError,
			                 "Only whitespace may be used for indentation.");
		return FALSE;
	}

    if (!encoder->colon) {
        if (encoder->indent_string == Py_None)
            encoder->colon = ascii_constant (": ", -1);
        else
            encoder->colon = ascii_constant (": ", -1);
        if (!encoder->colon) return FALSE;
    }
	
    if (!encoder->comma) {
        if (encoder->indent_string == Py_None)
            encoder->comma = ascii_constant (", ", -1);
        else
            encoder->comma = ascii_constant (", ", -1);
        if (!encoder->comma) return FALSE;
    }
	
	if ((encoder->UserString = jsonlib_import ("UserString", "UserString")) &&
	    (encoder->true_str = ascii_constant ("true", -1)) &&
	    (encoder->false_str = ascii_constant ("false", -1)) &&
	    (encoder->null_str = ascii_constant ("null", -1)) &&
	    (encoder->inf_str = ascii_constant ("Infinity", -1)) &&
	    (encoder->neg_inf_str = ascii_constant ("-Infinity", -1)) &&
	    (encoder->nan_str = ascii_constant ("NaN", -1)) &&
	    (encoder->quote = ascii_constant ("\"", -1)))
	{
		succeeded = write_object (encoder, value, 0, FALSE);
	}
	
	Py_XDECREF (encoder->UserString);
	Py_XDECREF (encoder->true_str);
	Py_XDECREF (encoder->false_str);
	Py_XDECREF (encoder->null_str);
	Py_XDECREF (encoder->inf_str);
	Py_XDECREF (encoder->neg_inf_str);
	Py_XDECREF (encoder->nan_str);
	Py_XDECREF (encoder->quote);
	Py_XDECREF (encoder->colon);
	Py_XDECREF (encoder->comma);
	
	return succeeded;
}

static void init_encoder(Encoder *encoder)
{
	encoder->sort_keys = FALSE;
	encoder->indent_string = Py_None;
	encoder->ensure_ascii = TRUE;
	encoder->coerce_keys = TRUE;
	encoder->default_handler = Py_None;
    encoder->allow_nan = TRUE;
    encoder->colon = NULL;
    encoder->comma = NULL;
    encoder->escape_slash = TRUE;
}

static PyObject*
_write_entry (PyObject *self, PyObject *args, PyObject *kwargs)
{
	PyObject *value;
	BufferEncoder encoder = {{NULL}, NULL};
	Encoder *encoder_base = (Encoder*) &encoder;
	char *encoding;
	
	static char *kwlist[] = {"value", "sort_keys", "indent",
	                         "ensure_ascii", "coerce_keys", "encoding",
	                         "default", "allow_nan", "escape_slash",
/*                              "check_circular", */
                             "separators",
                             NULL};
	
	/* Defaults */
    init_encoder(encoder_base);

	encoding = "utf-8";

    PyObject *separators=NULL;
    
	if (!PyArg_ParseTupleAndKeywords (args, kwargs, "O|iOiizOiiO:write",
	                                  kwlist,
	                                  &value,
	                                  &encoder_base->sort_keys,
	                                  &encoder_base->indent_string,
	                                  &encoder_base->ensure_ascii,
	                                  &encoder_base->coerce_keys,
	                                  &encoding,
	                                  &encoder_base->default_handler,
                                      &encoder_base->allow_nan,
                                      &encoder_base->escape_slash,
/*                                       &encoder_base->check_circular, */
                                      &separators)) {
            return NULL;
    }

    if (separators) {
        int result = PyArg_ParseTuple(separators, "OO:write",
                                      &encoder_base->comma,
                                      &encoder_base->colon);
        // ParseTuple uses borrowed refs
        if (!result) {
            return NULL;
        }
        Py_INCREF(encoder_base->comma);
        Py_INCREF(encoder_base->colon);
    }

    encoder_base->indent_string = normalize_indent_string(encoder_base->indent_string);
    
	encoder_base->append_ascii = buffer_encoder_append_ascii;
	encoder_base->append_unicode = buffer_encoder_append_unicode;
	if (serializer_init_and_run_common (encoder_base, value))
	{
		PyObject *retval;
		
		if (!(encoder.buffer_size > 0))
		{
			PyErr_SetString (PyExc_AssertionError,
			                 "encoder.buffer_size > 0");
			return NULL;
		}
		
		if (encoding == NULL)
		{
			retval = PyUnicode_FromUnicode (encoder.buffer,
			                                encoder.buffer_size);
		}
		
		else
		{
			retval = PyUnicode_Encode (encoder.buffer,
			                           encoder.buffer_size,
			                           encoding, "strict");
		}
		
		PyMem_Free (encoder.buffer);
		return retval;
	}
	return NULL;
}

static PyObject *
_dump_entry (PyObject *self, PyObject *args, PyObject *kwargs)
{
	PyObject *value;
	StreamEncoder encoder = {{NULL}, NULL};
	Encoder *encoder_base = (Encoder *) &encoder;
	
	static char *kwlist[] = {"value", "fp", "sort_keys", "indent",
	                         "ensure_ascii", "coerce_keys", "encoding",
	                         "default", "allow_nan",
/*                              "check_circular", */
                             "separators", NULL};
	
	/* Defaults */
    init_encoder(encoder_base);
    
	encoder.encoding = "utf-8";

    PyObject *separators=NULL;
	if (!PyArg_ParseTupleAndKeywords (args, kwargs, "OO|iOiizOiiO:dump",
	                                  kwlist,
	                                  &value,
	                                  &encoder.stream,
	                                  &encoder_base->sort_keys,
	                                  &encoder_base->indent_string,
	                                  &encoder_base->ensure_ascii,
	                                  &encoder_base->coerce_keys,
	                                  &encoder.encoding,
	                                  &encoder_base->default_handler,
                                      &encoder_base->allow_nan,
                                      &encoder_base->escape_slash,
/*                                       &encoder_base->check_circular, */
                                      &separators))
		return NULL;

    if (separators) {
        int result = PyArg_ParseTuple(separators, "OO:dump",
                                      &encoder_base->comma,
                                      &encoder_base->colon);

        if (!result) {
            return NULL;
        }
        Py_INCREF(encoder_base->comma);
        Py_INCREF(encoder_base->colon);
    }

    encoder_base->indent_string = normalize_indent_string(encoder_base->indent_string);
    
	encoder_base->append_ascii = stream_encoder_append_ascii;
	encoder_base->append_unicode = stream_encoder_append_unicode;
	if (serializer_init_and_run_common (encoder_base, value))
	{
		Py_INCREF (Py_None);
		return Py_None;
	}
	return NULL;
}

/* }}} */

/* python hooks {{{ */
static PyMethodDef module_methods[] = {
	{"read", (PyCFunction) (_read_entry), METH_VARARGS|METH_KEYWORDS,
	PyDoc_STR (
	"read (string)\n"
	"\n"
	"Parse a JSON expression into a Python value.\n"
	"\n"
	"If ``string`` is a byte string, it will be converted to Unicode\n"
	"before parsing.\n"
	"\n"
	)},
	
	{"dump", (PyCFunction) (_dump_entry), METH_VARARGS | METH_KEYWORDS,
	PyDoc_STR (
	"Serialize a Python value to a JSON-formatted byte string.\n"
	"\n"
	"Rather than being returned as a string, the output is written to\n"
	"a file-like object.\n"
	)},
	
	{"write", (PyCFunction) (_write_entry), METH_VARARGS|METH_KEYWORDS,
	PyDoc_STR (
	"write (value[, sort_keys[, indent[, ensure_ascii[, coerce_keys[, encoding[, default]]]]]])\n"
	"\n"
	"Serialize a Python value to a JSON-formatted byte string.\n"
	"\n"
	"value\n"
	"	The Python object to serialize.\n"
	"\n"
	"sort_keys\n"
	"	Whether object keys should be kept sorted. Useful\n"
	"	for tests, or other cases that check against a\n"
	"	constant string value.\n"
	"	\n"
	"	Default: False\n"
	"\n"
	"indent=None\n"
	"	A string to be used for indenting arrays and objects.\n"
	"	If this is non-None, pretty-printing mode is activated.\n"
	"	\n"
	"	Default: None\n"
	"\n"
	"ensure_ascii=True\n"
	"	Whether the output should consist of only ASCII\n"
	"	characters. If this is True, any non-ASCII code points\n"
	"	are escaped even if their inclusion would be legal.\n"
	"	\n"
	"	Default: True\n"
	"\n"
	"coerce_keys=True\n"
	"	Whether to coerce invalid object keys to strings. If\n"
	"	this is False, an exception will be raised when an\n"
	"	invalid key is specified.\n"
	"	\n"
	"	Default: False\n"
	"\n"
	"encoding='utf-8'\n"
	"	The output encoding to use. This must be the name of an\n"
	"	encoding supported by Python's codec mechanism. If\n"
	"	None, a Unicode string will be returned rather than an\n"
	"	encoded bytestring.\n"
	"	\n"
	"	If a non-UTF encoding is specified, the resulting\n"
	"	bytestring might not be readable by many JSON libraries,\n"
	"	including jsonlib2.\n"
	"	\n"
	"	The default encoding is UTF-8.\n"
	"\n"
	"default=None\n"
	"	An object that will be called to convert unknown values\n"
	"	into a JSON-representable value. The default simply raises\n"
	"	an UnknownSerializerError.\n"
    "\n"
    "allow_nan=True\n"
    "	Allow serialization of the python values inf (infinity), -inf\n"
    "	(negative infinity) and nan (not a number) as Infinity, -Infinity,\n"
    "	and NaN, respectively. Otherwise, will throw an exception\n"
	"\n"
    "escape_slash=True\n"
    "   Escape the '/' character in strings as '\\/'. This closes a\n"
    "   security hole when json is embedded directly into HTML.\n"
    "\n"
    )},
	{NULL, NULL}
};

PyDoc_STRVAR (module_doc,
	"Implementation of jsonlib2."
);

PyMODINIT_FUNC
initjsonlib2 (void)
{
	PyObject *module;
	PyObject *version, *read, *write;
	
	if (!(module = Py_InitModule3 ("jsonlib2", module_methods,
	                               module_doc)))
		return;
	
	if (!(ReadError = PyErr_NewException ("jsonlib2.ReadError",
	                                      PyExc_ValueError, NULL)))
		return;
	Py_INCREF (ReadError);
	PyModule_AddObject(module, "ReadError", ReadError);
	
	if (!(WriteError = PyErr_NewException ("jsonlib2.WriteError",
	                                       PyExc_ValueError, NULL)))
		return;
	Py_INCREF (WriteError);
	PyModule_AddObject(module, "WriteError", WriteError);
	
	if (!(UnknownSerializerError = PyErr_NewException ("jsonlib2.UnknownSerializerError",
	                                                   WriteError, NULL)))
		return;
	Py_INCREF (UnknownSerializerError);
	PyModule_AddObject(module, "UnknownSerializerError",
	                   UnknownSerializerError);
	
	/* Aliases */
	read = PyObject_GetAttrString (module, "read");
	write = PyObject_GetAttrString (module, "write");
	if (!(read && write))
		return;
	
	PyModule_AddObject (module, "loads", read);
	PyModule_AddObject (module, "dumps", write);
	
	/* If you change the version here, also change it in setup.py and
	 * jsonlib2.py.
	**/
	version = Py_BuildValue ("(iii)", 1, 3, 10);
	PyModule_AddObject (module, "__version__", version);
}
/* }}} */
