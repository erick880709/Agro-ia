# Evidencia ACC-07

| Criterio | Comprobación | Resultado |
|---|---|---|
| AC-01 | `GetAccountUseCaseTest#rejectsBlankId`, `#rejectsNullId` | passed |
| AC-02 | `GetAccountUseCaseTest#returnsAccountForOwner`, `#hidesAccountFromOtherUser` | passed |

Comando: `./gradlew :usecase:test` y `./gradlew validateStructure` → passed.
