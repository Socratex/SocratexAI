// PALETTE: the colours of every kind of block and state, and the small colour shift each
// session's tree gets. Pure data and maths, no decisions.
import type { Ring } from './model'

// Component colours (fill) and state colours (ring).
// `light` is the border of a component that is working right now.
export const KIND = {
  you: { fill: '#3b82f6', light: '#8ab4fa', text: '#ffffff' }, // blue
  claude: { fill: '#e8803a', light: '#f4a76b', text: '#1b1b1b' }, // orange
  agent: { fill: '#26c6da', light: '#7ee3ef', text: '#102027' }, // cyan
  tool: { fill: '#8e1b3a', light: '#c2476a', text: '#ffffff' }, // burgundy
  mcp: { fill: '#8e44ad', light: '#be7fd6', text: '#ffffff' }, // purple
  skill: { fill: '#f2c94c', light: '#f8e08e', text: '#1b1b1b' }, // yellow
  session: { fill: '#26c6da', light: '#7ee3ef', text: '#102027' }, // cyan, like a sub-agent
  app: { fill: '#e8803a', light: '#f4a76b', text: '#1b1b1b' }, // orange: the desktop app's own tools (ccd_*)
  side: { fill: '#ec4899', light: '#f59ac4', text: '#ffffff' }, // pink: a side fork a command started (/btw, /subtask)
  task: { fill: '#1e3a8a', light: '#4f6fc4', text: '#ffffff' }, // dark blue: a background command or monitor (/tasks)
}
export const STATE: Record<Ring, string> = {
  waiting: '#ff9800', // waiting for the user
  error: '#e53935',
  background: '#9e9e9e', // background work (grey)
}

export type Kind = keyof typeof KIND

// Every session gets its own small shift of the whole palette, so its tree reads
// as a family of its own: the hue moves a few degrees and the lightness a little
// up or down. The shift covers fills, active borders, glow, lines and dots (they
// all come from `palette`); state rings and text colours stay as they are,
// because they carry meaning. The root tree (this session) is never shifted.
const SHADES = [
  { hue: 0, light: 0 },
  { hue: 14, light: 0.05 },
  { hue: -14, light: -0.05 },
  { hue: 26, light: -0.04 },
  { hue: -26, light: 0.06 },
  { hue: 8, light: -0.08 },
  { hue: -8, light: 0.09 },
]

const hexToHsl = (hex: string): [number, number, number] => {
  const r = parseInt(hex.slice(1, 3), 16) / 255
  const g = parseInt(hex.slice(3, 5), 16) / 255
  const b = parseInt(hex.slice(5, 7), 16) / 255
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const l = (max + min) / 2
  const d = max - min
  if (d === 0) return [0, 0, l]
  const sat = d / (1 - Math.abs(2 * l - 1))
  const h = max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4

  return [(h * 60 + 360) % 360, sat, l]
}

const hslToHex = (h: number, s: number, l: number): string => {
  const c = (1 - Math.abs(2 * l - 1)) * s
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1))
  const m = l - c / 2
  const [r, g, b] = h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x] : h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x]
  const hex = (v: number): string => Math.round((v + m) * 255).toString(16).padStart(2, '0')

  return `#${hex(r)}${hex(g)}${hex(b)}`
}

const shiftHex = (hex: string, shade: number): string => {
  const sh = SHADES[shade <= 0 ? 0 : 1 + ((shade - 1) % (SHADES.length - 1))]!
  if (sh.hue === 0 && sh.light === 0) return hex
  const [h, s, l] = hexToHsl(hex)

  return hslToHex((h + sh.hue + 360) % 360, s, Math.min(0.9, Math.max(0.1, l + sh.light)))
}

// The colours of a kind in a session's shade (0 = the root tree, unshifted).
export const palette = (kind: Kind, shade = 0): { fill: string; light: string; text: string } => {
  const k = KIND[kind]

  return { fill: shiftHex(k.fill, shade), light: shiftHex(k.light, shade), text: k.text }
}
