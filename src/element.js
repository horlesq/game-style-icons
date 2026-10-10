// <game-icon set="cyberpunk" name="heart" size="32" label="Lives"></game-icon>
// A standard web component: works in plain HTML and in any framework. Loads one style module on first use.
const PREFIX = {"cyberpunk":"Cyberpunk","borderlands":"Borderlands","gta":"Gta","minecraft":"Minecraft","fallout":"Fallout","zelda":"Zelda","halo":"Halo","persona":"Persona","hollow-knight":"HollowKnight","hades":"Hades","portal":"Portal","mass-effect":"MassEffect","doom":"Doom","splatoon":"Splatoon","animal-crossing":"AnimalCrossing","hotline-miami":"Hotline","mirrors-edge":"MirrorsEdge","diablo":"Diablo","pac-man":"PacMan","overwatch":"Overwatch","super-mario":"SuperMario","sonic":"Sonic","pokemon":"Pokemon","tetris":"Tetris","space-invaders":"SpaceInvaders","undertale":"Undertale","asteroids":"Asteroids","kirby":"Kirby","final-fantasy":"FinalFantasy","among-us":"AmongUs","okami":"Okami","cuphead":"Cuphead","limbo":"Limbo","monument-valley":"MonumentValley","obra-dinn":"ObraDinn","firewatch":"Firewatch","nier-automata":"Nier","superhot":"Superhot","littlebigplanet":"LittleBigPlanet","bioshock":"Bioshock","the-witcher":"Witcher","elden-ring":"EldenRing","red-dead-redemption":"RedDead","assassins-creed":"AssassinsCreed","disco-elysium":"DiscoElysium","fortnite":"Fortnite","half-life":"HalfLife","dead-space":"DeadSpace","god-of-war":"GodOfWar","katamari":"Katamari"};
const pascal = (s) => s.split('-').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join('');
const cache = new Map();
const load = (set) => {
  if (!cache.has(set)) cache.set(set, import(`./html/${set}.js`));
  return cache.get(set);
};
const Base = typeof HTMLElement === 'undefined' ? class {} : HTMLElement;

export class GameIconElement extends Base {
  static get observedAttributes() { return ['set', 'name', 'size', 'label']; }
  connectedCallback() { this.render(); }
  attributeChangedCallback() { if (this.isConnected) this.render(); }
  async render() {
    const set = this.getAttribute('set'), name = this.getAttribute('name') || '';
    const label = this.getAttribute('label');
    const raw = (this.getAttribute('size') || '1em').replace(/[^0-9a-z.%]/gi, '');
    const size = /^[0-9.]+$/.test(raw) ? raw + 'px' : raw;
    if (label) { this.setAttribute('role', 'img'); this.setAttribute('aria-label', label); this.removeAttribute('aria-hidden'); }
    else { this.removeAttribute('role'); this.removeAttribute('aria-label'); this.setAttribute('aria-hidden', 'true'); }
    const root = this.shadowRoot || this.attachShadow({ mode: 'open' });
    const ticket = (this._ticket = (this._ticket || 0) + 1);
    const css = '<style>:host{display:inline-block;width:' + size + ';height:' + size + ';line-height:0;vertical-align:-0.125em}svg{display:block;width:100%;height:100%}</style>';
    if (!Object.prototype.hasOwnProperty.call(PREFIX, set)) { root.innerHTML = css; return; }
    let mod;
    try { mod = await load(set); } catch (e) { root.innerHTML = css; return; }
    if (ticket !== this._ticket) return;
    const icon = mod[PREFIX[set] + pascal(name)];
    root.innerHTML = css + (icon ? icon({ size: '100%' }) : '');
  }
}

if (typeof customElements !== 'undefined' && !customElements.get('game-icon')) customElements.define('game-icon', GameIconElement);
