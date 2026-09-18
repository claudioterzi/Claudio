"""JAX Engine — SDQ-1 core numerical backend.

Fornisce:
  - batch_cosine_similarity: ricerca vettoriale JIT su N documenti
  - MLP: rete feed-forward con grad automatico e vmap per-example
  - JAX_AVAILABLE: flag per degradazione graceful se JAX non è installato
"""

from __future__ import annotations

from typing import Any, List, Tuple, Optional

try:
    import jax
    import jax.numpy as jnp
    import jax.random as jr
    JAX_AVAILABLE = True
except ImportError:
    JAX_AVAILABLE = False


# ─────────────────────────────────────────────────────────────
# Batch cosine similarity
# ─────────────────────────────────────────────────────────────

if JAX_AVAILABLE:
    @jax.jit
    def _cosine_batch(query_vec: Any, doc_matrix: Any) -> Any:
        """
        query_vec : (vocab_size,)
        doc_matrix: (n_docs, vocab_size)
        returns   : (n_docs,) similarità coseno
        """
        dots = jnp.dot(doc_matrix, query_vec)
        q_norm = jnp.linalg.norm(query_vec)
        d_norms = jnp.linalg.norm(doc_matrix, axis=1)
        return dots / (q_norm * d_norms + 1e-8)

    def build_vocab_and_matrix(
        shingle_counters: list[dict[str, int]]
    ) -> Tuple[dict[str, int], Any]:
        """Costruisce vocabolario e matrice densa da lista di Counter."""
        vocab: dict[str, int] = {}
        for counter in shingle_counters:
            for token in counter:
                if token not in vocab:
                    vocab[token] = len(vocab)
        v = len(vocab)
        n = len(shingle_counters)
        rows = []
        for counter in shingle_counters:
            row = [0.0] * v
            for token, count in counter.items():
                row[vocab[token]] = float(count)
            rows.append(row)
        matrix = jnp.array(rows)  # (n, v)
        return vocab, matrix

    def counter_to_vec(counter: dict[str, int], vocab: dict[str, int]) -> Any:
        v = len(vocab)
        row = [0.0] * v
        for token, count in counter.items():
            if token in vocab:
                row[vocab[token]] = float(count)
        return jnp.array(row)


# ─────────────────────────────────────────────────────────────
# MLP con gradiente automatico e vmap per-example
# ─────────────────────────────────────────────────────────────

if JAX_AVAILABLE:
    Params = List[Tuple[Any, Any]]  # [(W, b), ...]

    def mlp_predict(params: Params, inputs: Any) -> Any:
        """Forward pass: tanh su tutti i layer tranne l'ultimo."""
        for W, b in params:
            outputs = jnp.dot(inputs, W) + b
            inputs = jnp.tanh(outputs)
        return outputs

    def mlp_loss(params: Params, inputs: Any, targets: Any) -> Any:
        """MSE loss."""
        preds = mlp_predict(params, inputs)
        return jnp.sum((preds - targets) ** 2)

    # Gradiente JIT compilato
    mlp_grad = jax.jit(jax.grad(mlp_loss))

    # Gradienti per-example (vmap su batch)
    mlp_perex_grads = jax.jit(jax.vmap(mlp_grad, in_axes=(None, 0, 0)))

    def mlp_init(
        layer_sizes: list[int],
        key: Optional[Any] = None,
        scale: float = 0.1,
    ) -> Params:
        """
        Inizializza parametri random per un MLP.
        layer_sizes = [input_dim, hidden1, ..., output_dim]
        """
        if key is None:
            key = jr.PRNGKey(0)
        params = []
        for in_sz, out_sz in zip(layer_sizes[:-1], layer_sizes[1:]):
            key, k1, k2 = jr.split(key, 3)
            W = jr.normal(k1, (in_sz, out_sz)) * scale
            b = jr.normal(k2, (out_sz,)) * scale
            params.append((W, b))
        return params

    def mlp_step(
        params: Params,
        inputs: Any,
        targets: Any,
        lr: float = 0.01,
    ) -> Tuple[Params, float]:
        """Un passo di gradient descent. Restituisce (new_params, loss)."""
        grads = mlp_perex_grads(params, inputs, targets)
        new_params = [
            (W - lr * gW.mean(0), b - lr * gb.mean(0))
            for (W, b), (gW, gb) in zip(params, grads)
        ]
        current_loss = float(mlp_loss(params, inputs, targets))
        return new_params, current_loss
