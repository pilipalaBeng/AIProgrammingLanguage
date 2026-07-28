import unittest

from lai_stdlib import (
    c_preamble,
    c_print_string_literal,
    c_print_value,
    escape_c_string,
)


class LaiStdlibTests(unittest.TestCase):
    def test_c_preamble_includes_required_headers(self):
        self.assertEqual(
            c_preamble(),
            ["#include <stdio.h>", "#include <string.h>"],
        )

    def test_escape_c_string_uses_c_string_literal_rules(self):
        self.assertEqual(escape_c_string('A "quote"\n'), '"A \\"quote\\"\\n"')

    def test_c_print_string_literal_appends_newline(self):
        self.assertEqual(
            c_print_string_literal("Hello LAI", "    "),
            '    printf("Hello LAI\\n");',
        )

    def test_c_print_value_uses_type_appropriate_format(self):
        self.assertEqual(c_print_value("string", "name", "  "), '  printf("%s\\n", name);')
        self.assertEqual(c_print_value("int", "count", "  "), '  printf("%d\\n", count);')
        self.assertEqual(c_print_value("bool", "ready", "  "), '  printf("%d\\n", ready);')

    def test_c_print_value_rejects_unknown_type(self):
        with self.assertRaisesRegex(ValueError, "unsupported printable LAI type: array"):
            c_print_value("array", "items", "    ")


if __name__ == "__main__":
    unittest.main()
