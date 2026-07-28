import unittest

from lai_stdlib import (
    c_preamble,
    c_print_string_literal,
    c_print_value,
    c_runtime_support,
    escape_c_string,
)


class LaiStdlibTests(unittest.TestCase):
    def test_c_preamble_includes_required_headers(self):
        self.assertEqual(
            c_preamble(),
            [
                "#include <stdio.h>",
                "#include <string.h>",
                "#include <limits.h>",
                "#include <stdint.h>",
                "#include <stdlib.h>",
            ],
        )

    def test_c_runtime_support_defines_checked_i32_helpers(self):
        support = "\n".join(c_runtime_support("__lai_test"))
        self.assertIn("#include <limits.h>", "\n".join(c_preamble()))
        self.assertIn("#include <stdint.h>", "\n".join(c_preamble()))
        self.assertIn("#include <stdlib.h>", "\n".join(c_preamble()))
        self.assertIn("static void __lai_test_runtime_error", support)
        self.assertIn("static int __lai_test_i32_add", support)
        self.assertIn("static int __lai_test_i32_subtract", support)
        self.assertIn("static int __lai_test_i32_multiply", support)
        self.assertIn("static int __lai_test_i32_negate", support)
        self.assertIn("static int __lai_test_i32_divide", support)
        self.assertIn("static int __lai_test_i32_modulo", support)
        self.assertIn('fprintf(stderr, "LAI runtime error: line %d: %s\\n"', support)
        self.assertIn("exit(EXIT_FAILURE);", support)

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
