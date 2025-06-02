import numpy as np
from matrix_hw_wrapper import matrix_mul_hw

def matrix_mul_sw(A, B):
    """
    A: numpy array of shape (M, K)
    B: numpy array of shape (K, N)
    Returns: numpy array of shape (M, N)
    """
    return np.dot(A, B)

def generate_random_matrices(M, K, N):
    """
    Generates two random matrices:
    A: shape (M, K)
    B: shape (K, N)
    """
    A = np.random.uniform(-1, 1, size=(M, K)).astype(np.float32)
    B = np.random.uniform(-1, 1, size=(K, N)).astype(np.float32)
    return A, B

def compare_results(C_sw, C_hw, atol=1e-3):
    """
    Compare two matrices with a tolerance
    """
    if np.allclose(C_sw, C_hw, atol=atol):
        print("✅ HW and SW results match within tolerance.")
    else:
        print("❌ Mismatch between HW and SW results.")
        diff = np.abs(C_sw - C_hw)
        print(f"Max difference: {np.max(diff)}")

def print_matrix(mat, label="Matrix"):
    """
    Nicely prints a 2D matrix with a label
    """
    print(f"\n{label} (shape {mat.shape}):")
    for row in mat:
        print("  " + "  ".join(f"{val:8.4f}" for val in row))

def main():
    # Set matrix sizes
    M, K, N = 2, 4, 2
    print(f"Generating random matrices: A({M},{K}), B({K},{N})")

    # Generate matrices
    A, B = generate_random_matrices(M, K, N)

    # SW multiply
    print("Running software matrix multiplication...")
    C_sw = matrix_mul_sw(A, B)
    print_matrix(C_sw, label="C_sw")

    # HW multiply via cocotb
    print("Running hardware matrix multiplication via cocotb...")
    C_hw = matrix_mul_hw(A, B)
    print_matrix(C_hw, label="C_hw")

    # Compare results
    compare_results(C_sw, C_hw)

if __name__ == "__main__":
    main()
