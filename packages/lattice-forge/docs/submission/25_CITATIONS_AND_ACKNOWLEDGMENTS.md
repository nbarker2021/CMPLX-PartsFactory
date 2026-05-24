# Citations and Acknowledgments

## Author

**Nicholas Barker**
Independent researcher

The lattice-forge framework and the chart-to-J₃(𝕆) isomorphism construction are original work by the author. The transport-of-structure technique is standard mathematics.

## Mathematical foundations (cited theorems used by transport)

### Lie theory

- **Cartan, É.** (1894). *Sur la structure des groupes de transformations finis et continus*. Doctoral thesis, École Normale Supérieure.
- **Killing, W.** (1888-1890). *Die Zusammensetzung der stetigen endlichen Transformationsgruppen*. Mathematische Annalen. — Classification of simple Lie algebras.
- **Freudenthal, H.** (1963). *Lie Groups in the Foundations of Geometry*. Advances in Mathematics 1, 145–190. — Tits-Freudenthal Magic Square.
- **Tits, J.** (1966). *Algèbres alternatives, algèbres de Jordan et algèbres de Lie exceptionnelles*. Indagationes Mathematicae 28, 223–237.
- **Fulton, W., Harris, J.** (1991). *Representation Theory: A First Course*. Springer GTM 129. — Standard reference for E₆, E₇, E₈.

### Jordan algebras

- **Jordan, P., von Neumann, J., Wigner, E.** (1934). *On an algebraic generalization of the quantum mechanical formalism*. Annals of Mathematics 35, 29–64. — Classification of formally real Jordan algebras.
- **Jacobson, N.** (1968). *Structure and Representations of Jordan Algebras*. AMS Colloquium Publications 39. — Standard reference for J₃(𝕆).
- **Zel'manov, E.** (1983). *Jordan division algebras*. Algebra i Logika 22(3), 286–305. — Uniqueness theorems.

### Octonions

- **Hurwitz, A.** (1898). *Über die Composition der quadratischen Formen von beliebig vielen Variabeln*. Nachrichten von der Gesellschaft der Wissenschaften zu Göttingen. — Normed division algebras classification.
- **Eckmann, B.** (1942). *Stetige Lösungen linearer Gleichungssysteme*. Commentarii Mathematici Helvetici 15, 318–339. — 3D and 7D cross product uniqueness.
- **Baez, J.** (2002). *The Octonions*. Bulletin of the AMS 39(2), 145–205. — Accessible modern survey.

### Sphere eversion / topology

- **Smale, S.** (1958). *A classification of immersions of the two-sphere*. Transactions of the AMS 90, 281–290. — Sphere eversion existence.
- **Phillips, A.** (1966). *Turning a surface inside out*. Scientific American 214(5), 112–120. — Explicit construction.

### Monstrous Moonshine

- **Conway, J. H., Norton, S. P.** (1979). *Monstrous Moonshine*. Bulletin of the London Mathematical Society 11, 308–339.
- **Borcherds, R.** (1992). *Monstrous Moonshine and monstrous Lie superalgebras*. Inventiones Mathematicae 109, 405–444. — Proof of the Conway-Norton conjecture.

### Lattices

- **Conway, J. H., Sloane, N. J. A.** (1999). *Sphere Packings, Lattices and Groups* (3rd ed.). Springer. — Standard reference for E₈ and Niemeier lattices.
- **Niemeier, H.-V.** (1973). *Definite quadratische Formen der Dimension 24 und Diskriminante 1*. Journal of Number Theory 5, 142–178. — Classification of 24D even unimodular lattices.

### Cellular automata

- **Wolfram, S.** (1983). *Statistical mechanics of cellular automata*. Reviews of Modern Physics 55(3), 601–644. — Original Rule 30 paper.
- **Wolfram, S.** (2002). *A New Kind of Science*. Wolfram Media.
- **Wolfram, S.** (2019). *Announcing the Rule 30 Prizes*. Stephen Wolfram Writings (October 1, 2019). [Available online](https://writings.stephenwolfram.com/2019/10/announcing-the-rule-30-prizes/)

## Software / framework references

- The lattice-forge framework (this submission): Python 3.10+, pure stdlib for the proof primitives, FastAPI for the optional server.
- The CMPLX corpus (author's working archives): predates this submission, provides organizing vocabulary (MFT, NSL, morphonics framework).
- The Aletheia / CQE / MDHG / MMDB / SpeedLight services (substrate pipeline): docker-deployed reference architecture.

## Acknowledgments

The author thanks the prize committee for accepting submissions in non-standard mathematical registers. The chart-to-J₃(𝕆) isomorphism approach is non-traditional but uses entirely standard underlying mathematics (Lie theory, Jordan algebras, transport of structure).

The author acknowledges that aspects of the broader morphonics framework (MFT, NSL, post-VN substrate) are research-program-level claims that go beyond the prize problem's scope. The submission's prize-relevant content is intentionally limited to the proven theorems (T1-T8) and the transported conclusions for Problems 1 and 2.

## Conflict of interest disclosure

The author has no commercial or institutional affiliations relevant to the prize. The work is independent research. The author is not affiliated with Wolfram Research or any organization that benefits financially from prize outcomes.

## Contact

For verification queries, reproduction issues, or follow-up discussion, the author is available at the contact information provided with the prize submission. The executable build (Zip 2) is self-contained and reproducible by any reviewer with Python 3.10+.

## License

The lattice-forge framework code is released under the license specified in `LICENSE.txt` in the executable build package. The text of the submission documents is released under CC BY 4.0 for academic reuse.

---

*End of theory & papers package. Continue with the executable build package for code and verification harness.*
