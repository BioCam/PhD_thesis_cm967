# De Novo Orthogonal Oligo Generator (DeNOOG)

* **Author**: Camillo Moschner
* **Aim**: simple programme to generate ssDNA oligos that are highly orthogonal to themselves and other DNA
* **Common use cases**:
  1. Primer design for PCRs
  2. Flanking primer design for ordered DNA; allows client-specified amplification (redundancy if DNA synthesis company uses good flanking sequences; absolute must if they don't)
  3. Design of FISH readout probes (i.e. the ssDNA oligo-fluorophore)

---

## Installations/Dependencies

DeNOOG requires the following Python libraries to be installed:

### NUPACK

NUPACK is a software suite that is used for the design, analysis, and prediction of the behavior of nucleic acid systems. It is commonly used in the field of nucleic acid nanotechnology, which involves the design and construction of structures made from DNA or RNA.
NUPACK provides a range of tools for simulating the behavior of nucleic acid systems, including predicting secondary structure, thermodynamic properties, and strand displacement. 
It also includes tools for designing and optimizing oligonucleotide sequences for a variety of applications, such as PCR, RNA interference, and aptamer selection.

To install NUPACK you have to create a NUPACK account, choose a subscription model (at the moment even though it looks like you have to pay, you don't have to yet.
I emailed the developers and the payment system is not yet active. Instead click on a [license](https://www.nupack.org/download/license), and just download the package.
Then follow the [installation guide](https://docs.nupack.org/start/#maclinux-installation). The main command is:

```bash
pip install -U nupack -f /Users/camillomoschner/Desktop/nupack-4.0.1.8/package
```

### seqfold, biopython, levenstein (standard PIP installs)

[seqfold](https://pypi.org/project/seqfold/)
```bash
pip install seqfold
```

[biopython](https://pypi.org/project/biopython/)
```bash
pip install biopython
```

[levenshtein](https://maxbachmann.github.io/Levenshtein/installation.html)
```bash
pip install levenshtein
```

---

<!-- ## Functionalities -->

## Required functionalities
 1. Sequence properties:
 2. Orthogonality
    1. Intra-molecule orthogonality
    2. Homogeneous inter-molecule orthogonality
    3. Heterogeneous inter-molecule orthogonality


## De novo oligo design



## Template-based oligo design

*  **Aim**: generate ideal primers based on a string of template dsDNA
* **Input**: string of DNA in forward orientation to where the primer is supposed to go (multiple hundreds of bp for screening primer sites)
* **Output**: list of well behaving primers

* **Algorithm overview**:
  1. Moving window:
    1. slices given DNA string into segments of length as asked for
    2. tests each segment for sequence property agreement & orthogonality metrics
