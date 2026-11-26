// PANE: the elements of the pane (the figure toggle and the drawing). Takes ready data, reads
// nothing and decides nothing: the picture is made by draw.ts, the choice is the person's.
import type { Figure } from '../types'
import { FIGURES } from './model'

// The toggle: one icon per measure; the chosen one is lit, the others dim.
const FIGURE_ICON: Record<Figure, string> = { cost: '$', time: '◷', tokens: '❐' }

// The surface's own elements (`$.ui.resolve(e)`), as the pane needs them.
type Elements = { Box: any; Text: any; Svg?: any; Button?: any }

export const paneTree = ({ Box, Text, Svg, Button }: Elements, source: string, figure: Figure, onPick: (f: Figure) => void) => {
  // Without an explicit size the pane seems to cap the drawing's height and
  // shrink a taller one, so state the drawing's own size.
  const size = /width="([\d.]+)" height="([\d.]+)"/.exec(source)

  return (
    <Box flexDirection="column" alignItems="flex-start" width="100%">
      {Button ? (
        // Centred over the drawing, a gap below it, no background of its own.
        <Box width="100%" justifyContent="center" marginBottom="md">
          <Box borderStyle="round" paddingX="sm" gap="md">
            {FIGURES.map(f => (
              <Button
                key={`figure-${f}`}
                label={FIGURE_ICON[f]}
                // `plain` would draw both states alike, so the lit one is the primary button.
                variant={f === figure ? 'primary' : 'secondary'}
                dimColor={f !== figure}
                onPress={() => onPick(f)}
              />
            ))}
          </Box>
        </Box>
      ) : null}
      {Svg ? (
        <Svg
          source={source}
          width={size ? Number(size[1]) : undefined}
          height={size ? Number(size[2]) : undefined}
          alt="Live graph: you, Claude and the sub-agents, tools, MCP servers and skills it uses, with the limit cost on each line"
          isInteractive
        />
      ) : (
        <Text dimColor>This surface has no Svg element.</Text>
      )}
    </Box>
  )
}
