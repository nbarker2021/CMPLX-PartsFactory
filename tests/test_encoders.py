"""Test suite for E8 lattice encoders (Chunk 2)."""
import numpy as np
import pytest
import sys
import os

# Ensure CMPLX-PartsFactory src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cmplx.lattice import (
    E8Lattice, E8WeylGroup, E8Root, E8RootType,
    E8Encoder,
    encode_phi_psi, encode_hash, encode_genome, encode_prime,
    encode_gauss_code, encode_species, encode_velocity, encode_gap,
    encode_chromophore_state, encode_user, encode_element,
    encode_system_state, encode_gps_state, encode_drug,
    encode_target_window, encode_density_point, encode_cdr3,
    encode_institution,
)


class TestE8TypeHintsFixed:
    """Verify that TYPE_D roots with half-integer coords now pass."""

    def test_type_d_root_creation(self):
        """TYPE_D roots have float coords; must not raise on __post_init__."""
        root = E8Root((0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5), E8RootType.TYPE_D, 112)
        assert root.norm_squared() == pytest.approx(2.0)
        assert isinstance(root.coords, tuple)
        assert all(isinstance(c, float) for c in root.coords)

    def test_type_a_root_creation(self):
        """TYPE_A roots still work with integer-looking floats."""
        root = E8Root((1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), E8RootType.TYPE_A, 0)
        assert root.norm_squared() == pytest.approx(2.0)

    def test_weyl_group_generates_240(self):
        weyl = E8WeylGroup()
        assert len(weyl.root_system) == 240

    def test_lattice_minimal_vectors(self):
        lat = E8Lattice()
        assert len(lat.minimal_vectors) == 240


class TestRawEncoders:
    """All raw encoders must return 8D numpy arrays."""

    def _assert_8d(self, vec):
        assert isinstance(vec, np.ndarray)
        assert vec.shape == (8,)
        assert vec.dtype == np.float64 or vec.dtype == np.float32

    def test_encode_phi_psi(self):
        self._assert_8d(encode_phi_psi(0.5, 1.0))

    def test_encode_hash(self):
        self._assert_8d(encode_hash("hello"))
        self._assert_8d(encode_hash(b"hello"))

    def test_encode_genome(self):
        self._assert_8d(encode_genome("ATGCGTAC"))
        self._assert_8d(encode_genome(""))

    def test_encode_prime(self):
        self._assert_8d(encode_prime(97))

    def test_encode_gauss_code(self):
        self._assert_8d(encode_gauss_code(3, [1, -2, 3]))

    def test_encode_species(self):
        self._assert_8d(encode_species(100.0, 0.5, 0.2, 3.0, ["A", "B"], 1.0))

    def test_encode_velocity(self):
        self._assert_8d(encode_velocity(1, 2, 3, 0.1, 0.2, 0.3, 0.4, 0.5))

    def test_encode_gap(self):
        self._assert_8d(encode_gap(0.5, 1.0, 0.0, 0.3, 0.1, 0.9, 0.2))

    def test_encode_chromophore_state(self):
        self._assert_8d(encode_chromophore_state(400.0, [10.0, 20.0, 30.0], 0.8))

    def test_encode_user(self):
        v1 = encode_user(42, 0.5, 0.8, 0.2)
        self._assert_8d(v1)
        v2 = encode_user(42, 0.5, 0.8, 0.2)
        # Same seed → same noise
        np.testing.assert_allclose(v1, v2)

    def test_encode_element(self):
        self._assert_8d(encode_element([6, 140, 1.7, 2.0, 8.0, 1.5, 0.6, 4.5]))
        self._assert_8d(encode_element([6, 140]))  # padding

    def test_encode_system_state(self):
        self._assert_8d(encode_system_state([0.1, 0.2, 0.3], [[0, 1], [1, 0]], 1.0))

    def test_encode_gps_state(self):
        self._assert_8d(encode_gps_state(10.0, 20.0, 5.0, 0.5, 0.0))

    def test_encode_drug(self):
        self._assert_8d(encode_drug([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]))

    def test_encode_target_window(self):
        self._assert_8d(encode_target_window([[1, 2, 3, 4, 5]] * 8))

    def test_encode_density_point(self):
        self._assert_8d(encode_density_point(0.5, [0.1, 0.2, 0.3], [100, 200, 300], 0.4, 0.1, 0.2))

    def test_encode_cdr3(self):
        self._assert_8d(encode_cdr3("CASSY"))
        self._assert_8d(encode_cdr3(""))

    def test_encode_institution(self):
        self._assert_8d(encode_institution(10.0, 0.5, 0.3, 1000.0, 0.02, 0.7, 12.0, 0.05))


class TestE8Encoder:
    """Lattice-aware encoder tests."""

    @pytest.fixture
    def encoder(self):
        return E8Encoder()

    def test_snap_to_root_range(self, encoder):
        for _ in range(20):
            vec = np.random.randn(8)
            idx = encoder.snap_to_root(vec)
            assert 0 <= idx < 240

    def test_encode_cooccurrence(self, encoder):
        vec = encoder.encode_cooccurrence(["hello", "world", "test"])
        assert isinstance(vec, np.ndarray)
        assert vec.shape == (8,)

    def test_encode_fingerprint(self, encoder):
        fp = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        idx = encoder.encode_fingerprint(fp)
        assert isinstance(idx, int)
        assert 0 <= idx < 240

    def test_place_helpers(self, encoder):
        """All place_* helpers return valid root indices."""
        assert 0 <= encoder.place_phi_psi(0.5, 1.0) < 240
        assert 0 <= encoder.place_hash("test") < 240
        assert 0 <= encoder.place_genome("ATGC") < 240
        assert 0 <= encoder.place_prime(101) < 240
        assert 0 <= encoder.place_gauss_code(3, [1, -2, 3]) < 240
        assert 0 <= encoder.place_species(10.0, 0.1, 0.2, 1.0, [], 1.0) < 240
        assert 0 <= encoder.place_velocity(1, 2, 3, 0, 0, 0, 0, 0) < 240
        assert 0 <= encoder.place_gap(0, 1, 0, 0.5, 0.1, 0.9, 0) < 240
        assert 0 <= encoder.place_chromophore_state(400, [10, 20, 30], 0.8) < 240
        assert 0 <= encoder.place_user(1, 0.0, 0.0, 0.0) < 240
        assert 0 <= encoder.place_element([6, 140, 1.7, 2.0, 8.0, 1.5, 0.6, 4.5]) < 240
        assert 0 <= encoder.place_system_state([0.1], [[0]], 0) < 240
        assert 0 <= encoder.place_gps_state(0, 0, 0, 0, 0) < 240
        assert 0 <= encoder.place_drug([0.5] * 8) < 240
        assert 0 <= encoder.place_target_window([[0.5] * 5] * 8) < 240
        assert 0 <= encoder.place_density_point(0, [0, 0, 0], [0, 0, 0], 0, 0, 0) < 240
        assert 0 <= encoder.place_cdr3("CASSY") < 240
        assert 0 <= encoder.place_institution(10, 0.5, 0.3, 100, 0.02, 0.7, 12, 0.05) < 240


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
