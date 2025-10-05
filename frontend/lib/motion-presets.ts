import type { MotionProps, Variants, Transition } from "framer-motion";

export const easeOutExpo: Transition["ease"] = [0.16, 1, 0.3, 1];

export const pageContainerVariants: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.45,
      ease: easeOutExpo,
      when: "beforeChildren",
      staggerChildren: 0.04,
    },
  },
  exit: {
    opacity: 0,
    y: -16,
    transition: {
      duration: 0.3,
      ease: easeOutExpo,
    },
  },
};

export const sectionVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: easeOutExpo,
    },
  },
};

export const staggerContainer: Variants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
};

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 18 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.35,
      ease: easeOutExpo,
    },
  },
};

export const fadeInScale: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.3,
      ease: easeOutExpo,
    },
  },
};

export const hoverLift: MotionProps = {
  whileHover: {
    y: -6,
    scale: 1.01,
    transition: { duration: 0.2, ease: easeOutExpo },
  },
  whileTap: {
    scale: 0.99,
    transition: { duration: 0.1, ease: "linear" },
  },
};

export const subtleHover: MotionProps = {
  whileHover: {
    scale: 1.015,
    transition: { duration: 0.2, ease: easeOutExpo },
  },
  whileTap: {
    scale: 0.995,
    transition: { duration: 0.1, ease: "linear" },
  },
};

export const fadeInPresence: Variants = {
  hidden: { opacity: 0, y: 6 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.25, ease: easeOutExpo },
  },
  exit: {
    opacity: 0,
    y: -6,
    transition: { duration: 0.2, ease: easeOutExpo },
  },
};

export const scaleInPresence: Variants = {
  hidden: { opacity: 0, scale: 0.96 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.25, ease: easeOutExpo },
  },
  exit: {
    opacity: 0,
    scale: 0.96,
    transition: { duration: 0.2, ease: easeOutExpo },
  },
};

export const defaultPageMotion: MotionProps = {
  variants: pageContainerVariants,
  initial: "hidden",
  animate: "visible",
  exit: "exit",
};

export const staggeredListMotion: MotionProps = {
  variants: staggerContainer,
  initial: "hidden",
  animate: "visible",
};

export const fadeInItemMotion: MotionProps = {
  variants: fadeInUp,
};

