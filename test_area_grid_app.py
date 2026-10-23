import unittest

from area_grid_app import (
    FormulaError,
    group_expression,
    parse_expression,
    piece_terms,
    vertical_steps,
)


class FormulaParserTests(unittest.TestCase):
    def test_plain_dimensions_are_split_automatically(self) -> None:
        model = parse_expression("16×12")
        self.assertEqual(model.display_expression, "16×12")
        self.assertEqual(model.width_parts, (10, 6))
        self.assertEqual(model.height_parts, (10, 2))
        self.assertEqual(
            piece_terms(model),
            [(10, 10, 100), (6, 10, 60), (10, 2, 20), (6, 2, 12)],
        )
        self.assertEqual(vertical_steps(model), [(1, 2, 32), (0, 10, 160)])
        self.assertEqual(group_expression(model, 1), "（10×2）＋（6×2）")
        self.assertEqual(group_expression(model, 0), "（10×10）＋（6×10）")

    def test_requested_example(self) -> None:
        model = parse_expression("16×12=(10+6)×(10+2)")
        self.assertEqual(model.display_expression, "16×12")
        self.assertEqual(model.total_width, 16)
        self.assertEqual(model.total_height, 12)
        self.assertEqual(model.width_parts, (10, 6))
        self.assertEqual(model.height_parts, (10, 2))
        self.assertEqual(
            piece_terms(model),
            [(10, 10, 100), (6, 10, 60), (10, 2, 20), (6, 2, 12)],
        )

    def test_ascii_multiplication_symbols(self) -> None:
        model = parse_expression("(7+3) * (4+2)")
        self.assertEqual((model.total_width, model.total_height), (10, 6))

    def test_single_rectangle(self) -> None:
        model = parse_expression("8x5")
        self.assertEqual(model.width_parts, (8,))
        self.assertEqual(model.height_parts, (5,))

    def test_exact_tens_are_not_split_with_zero(self) -> None:
        model = parse_expression("20x15")
        self.assertEqual(model.width_parts, (20,))
        self.assertEqual(model.height_parts, (10, 5))

    def test_larger_number_splits_into_tens_part_and_ones(self) -> None:
        model = parse_expression("123x45")
        self.assertEqual(model.width_parts, (120, 3))
        self.assertEqual(model.height_parts, (40, 5))

    def test_mismatched_equation_is_rejected(self) -> None:
        with self.assertRaises(FormulaError):
            parse_expression("15×12=(10+6)×(10+2)")

    def test_unbalanced_parentheses_are_rejected(self) -> None:
        with self.assertRaises(FormulaError):
            parse_expression("(10+6×(10+2)")


if __name__ == "__main__":
    unittest.main()
