# Limitations

## Honest scope

PNVA-Core esta validado como arquitetura experimental local com evidencia de campo vivo. A publicacao deve evitar afirmacoes absolutas.

## Claims allowed

```text
Validado em campo vivo local com gates longos e production-candidate PASS.
```

```text
Arquitetura event-aware/no-tick com provas JSON auditaveis.
```

```text
Modelo causal: estado, evento, tensao, colapso e prova.
```

## Claims not allowed yet

```text
Provado universalmente.
```

```text
Substitui todo tick do kernel Linux.
```

```text
Garante economia de energia em qualquer computador.
```

```text
Melhora todo jogo, minerador ou workload.
```

## Reclassification note

O 24h foi PASS canonico. O bruto registrou FAIL por ultimo snapshot em `WARMUP`. Essa diferenca precisa ficar visivel em qualquer paper, README ou apresentacao.

## External validation needed

Para reconhecimento mais forte:

1. Rodar em hardware diferente.
2. Rodar em distro diferente.
3. Rodar com perfil limpo sem desktop ativo.
4. Comparar contra daemon polling equivalente.
5. Publicar scripts de reproducao minimalistas.
6. Receber reproducao externa via issue/PR.

