// Type declarations for press.mjs — the runtime source lives in press.mjs so
// Node build scripts (and, via the emitted press.json, the Python Worker) can
// consume it without a TS toolchain.

export type PressItem = {
  readonly outlet: string;
  readonly title: string;
  readonly dek: string;
  readonly href: string;
};

export const PRESS: ReadonlyArray<PressItem>;
