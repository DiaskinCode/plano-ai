// Animation utilities - v0 inspired patterns

// Constants
export * from './constants';

// Pool management for limiting concurrent animations
export { createUsePool, useMessageFadePool, useTextFadePool, useListItemPool } from './usePool';

// Staggered animation scheduling
export { createUseStaggered, useMessageStagger, useTextStagger, useListStagger } from './useStaggeredAnimation';

// Fade-in components
export {
  FadeIn,
  FadeInStaggered,
  FadeInIfStreaming,
  FadeInSlide,
} from './FadeInStaggered';

// Text fade-in components
export {
  TextFadeInStaggeredIfStreaming,
  DisableFadeProvider,
  useDisableFadeContext,
} from './TextFadeInStaggered';

// New staggered fade system (v0 inspired)
export {
  useTextFadePool as useTextFadePoolV2,
  useElementFadePool,
  useFadeInAnimation,
} from './staggeredFade';
