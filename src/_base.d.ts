import * as React from 'react';

export interface GameIconProps extends Omit<React.SVGProps<SVGSVGElement>, 'ref'> {
  /** Width and height. Default '1em', so the icon follows the font size. */
  size?: string | number;
  /** Accessible name. Without it the icon is hidden from screen readers. */
  title?: string;
}
export type GameIcon = React.ForwardRefExoticComponent<GameIconProps & React.RefAttributes<SVGSVGElement>>;
export declare function createIcon(name: string, viewBox: string, markup: string): GameIcon;
