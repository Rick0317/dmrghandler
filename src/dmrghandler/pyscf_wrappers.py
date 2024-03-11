"""Wrappers for pyscf"""

import logging

log = logging.getLogger(__name__)
import numpy as np
import pyscf
import pyscf.fci


def get_pyscf_mol(basis, geometry, num_unpaired_electrons, charge, multiplicity):
    mol = pyscf.gto.Mole()
    mol.basis = basis
    mol.atom = geometry
    mol.spin = num_unpaired_electrons
    mol.charge = charge
    mol.multiplicity = multiplicity
    mol.build()

    return mol


def get_pyscf_tensors(mol):
    # Get one and two body tensors
    # Based on the approach used in Block2 in get_rhf_integrals
    # of pyblock2/_pyscf/ao2mo/integrals.py at https://github.com/block-hczhai/block2-preview
    ##################
    myhf = mol.RHF().run()
    mo_coeff = myhf.mo_coeff
    mo_coeff_julia = mo_coeff
    h_core_julia = myhf.get_hcore()
    one_body_tensor = mo_coeff_julia.T @ h_core_julia @ mo_coeff_julia

    num_orbitals = mol.nao_nr()
    g2e = pyscf.ao2mo.full(myhf._eri, mo_coeff)
    two_body_tensor = pyscf.ao2mo.restore(symmetry="s1", eri=g2e, norb=num_orbitals)

    nuc_rep_energy = mol.energy_nuc()
    return one_body_tensor, two_body_tensor, nuc_rep_energy


def get_pyscf_fci_energy(mol):

    # Get FCI energies, code mostly from https://pyscf.org/user/ci.html
    ##################
    myhf = mol.RHF().run()

    #
    # create an FCI solver based on the SCF object
    #
    cisolver = pyscf.fci.FCI(myhf)
    E_FCI_HF = cisolver.kernel()[0]

    #
    # create an FCI solver based on the SCF object
    #
    myuhf = mol.UHF().run()
    cisolver = pyscf.fci.FCI(myuhf)
    E_FCI_UHF = cisolver.kernel()[0]

    #
    # create an FCI solver based on the given orbitals and the num. electrons and
    # spin of the mol object
    #
    cisolver = pyscf.fci.FCI(mol, myhf.mo_coeff)
    E_FCI_orb = cisolver.kernel()[0]

    return E_FCI_HF, E_FCI_UHF, E_FCI_orb


def one_body_tensor_orbital_to_spin_orbital(one_body_tensor):
    num_orbitals = one_body_tensor.shape[0]
    one_body_tensor_spin_orbital = np.zeros((2 * num_orbitals, 2 * num_orbitals))
    for piter in range(num_orbitals):
        for qiter in range(num_orbitals):
            one_body_tensor_spin_orbital[2 * piter, 2 * qiter] = one_body_tensor[
                piter, qiter
            ]
            one_body_tensor_spin_orbital[2 * piter + 1, 2 * qiter + 1] = (
                one_body_tensor[piter, qiter]
            )

    return one_body_tensor_spin_orbital


def two_body_tensor_orbital_to_spin_orbital(two_body_tensor):
    num_orbitals = two_body_tensor.shape[0]
    two_body_tensor_spin_orbital = np.zeros(
        (2 * num_orbitals, 2 * num_orbitals, 2 * num_orbitals, 2 * num_orbitals)
    )
    for piter in range(num_orbitals):
        for qiter in range(num_orbitals):
            for riter in range(num_orbitals):
                for siter in range(num_orbitals):
                    two_body_tensor_spin_orbital[
                        2 * piter, 2 * qiter, 2 * riter, 2 * siter
                    ] = two_body_tensor[piter, qiter, riter, siter]
                    two_body_tensor_spin_orbital[
                        2 * piter + 1, 2 * qiter + 1, 2 * riter + 1, 2 * siter + 1
                    ] = two_body_tensor[piter, qiter, riter, siter]
                    two_body_tensor_spin_orbital[
                        2 * piter, 2 * qiter, 2 * riter + 1, 2 * siter + 1
                    ] = two_body_tensor[piter, qiter, riter, siter]
                    two_body_tensor_spin_orbital[
                        2 * piter + 1, 2 * qiter + 1, 2 * riter, 2 * siter
                    ] = two_body_tensor[piter, qiter, riter, siter]
    return two_body_tensor_spin_orbital
