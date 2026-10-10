export interface IconStringOptions {
  /** Width and height. Default '1em', so the icon follows the font size. */
  size?: string | number;
  /** Accessible name. Without it the icon gets aria-hidden. */
  title?: string;
  /** Class attribute for the <svg>. */
  class?: string;
  /** Any other attributes for the <svg>. */
  attrs?: Record<string, string | number>;
}
/** Returns the icon as an SVG string. */
export type IconString = (options?: IconStringOptions) => string;
export declare function createIconString(viewBox: string, markup: string): IconString;
