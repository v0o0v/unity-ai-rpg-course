import json
import unittest
from pathlib import Path
from reference_contracts import world2d, world3d, cell_of, damage, progression, grid_path

class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads((Path(__file__).resolve().parents[1]/'game_fixtures/parity_examples.json').read_text())

    def test_coordinate_fixture(self):
        for c in self.fixture['coordinateCases']:
            self.assertEqual(list(world2d(*c['logical'])),c['world2D'])
            self.assertEqual(list(world3d(*c['logical'])),c['world3D'])

    def test_negative_cells_use_floor(self):
        self.assertEqual(cell_of(-0.01,-1.01),(-1,-2))
        self.assertEqual(cell_of(0.99,0.99),(0,0))

    def test_damage_fixture_and_half_up(self):
        for c in self.fixture['damageCases']:
            self.assertEqual(damage(c['raw'],c['armor']),c['expected'])

    def test_xp_and_cap(self):
        for c in self.fixture['progressionCases']:
            self.assertEqual(progression(c['totalXp']),(c['level'],c['remainder']))
        self.assertEqual(progression(999999),(10,0))

    def test_spin_eight_times(self):
        self.assertEqual(self.fixture['spinTickTimes'],[i/4 for i in range(1,9)])

    def test_no_diagonal_corner_cut(self):
        self.assertIsNone(grid_path(2,2,{(1,0),(0,1)},(0,0),(1,1)))

    def test_wall_detour_is_deterministic(self):
        args=(6,5,{(2,y) for y in range(4)},(0,0),(5,0))
        a=grid_path(*args)
        self.assertIsNotNone(a)
        self.assertEqual(a,grid_path(*args))
        self.assertTrue(any(y==4 for x,y in a))

    def test_budget_is_not_unreachable(self):
        with self.assertRaises(TimeoutError):
            grid_path(8,8,[],(0,0),(7,7),1)

    def test_invalid_input(self):
        with self.assertRaises(ValueError): cell_of(0,0,0)
        with self.assertRaises(ValueError): damage(float('nan'),0)
        with self.assertRaises(ValueError): progression(-1)

if __name__=='__main__': unittest.main()
