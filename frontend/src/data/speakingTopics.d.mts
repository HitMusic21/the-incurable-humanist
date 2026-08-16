// Type declarations for speakingTopics.mjs — the runtime source lives in
// speakingTopics.mjs so Node build scripts can import it without a TS toolchain.

export type SpeakingTopic = {
  readonly slug: string;
  readonly title: string;
  readonly subtitle: string;
  readonly audience: string;
  readonly blurb: string;
  readonly keywords: readonly string[];
};

export const SPEAKING_TOPICS: ReadonlyArray<SpeakingTopic>;
