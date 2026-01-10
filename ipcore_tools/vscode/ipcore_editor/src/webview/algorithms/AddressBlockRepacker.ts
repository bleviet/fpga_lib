/**
 * Address block repacking algorithms for maintaining proper block layouts
 */

/**
 * Repack address blocks forward (toward higher addresses) starting from the given index.
 * Maintains block sizes but shifts them to higher addresses.
 * Calculates block size based on number of registers (4 bytes per register).
 * @param blocks Array of address blocks
 * @param fromIndex Starting index for repacking (inclusive)
 * @returns New array with repacked blocks
 */
export function repackBlocksForward(blocks: any[], fromIndex: number): any[] {
  const newBlocks = [...blocks];

  // Start from the block just before fromIndex to determine the starting position
  let nextBase = 0;
  if (fromIndex > 0) {
    const prevBlock = newBlocks[fromIndex - 1];
    const prevBase = typeof prevBlock.base_address === 'number' ? prevBlock.base_address : 0;

    // Calculate size based on registers (4 bytes per register)
    const prevRegisters = prevBlock.registers || [];
    const prevSize = prevRegisters.length > 0
      ? prevRegisters.length * 4
      : (typeof prevBlock.size === 'number' ? prevBlock.size : 4);

    nextBase = prevBase + prevSize;
  }

  for (let i = fromIndex; i < newBlocks.length; i++) {
    const block = newBlocks[i];

    // Calculate size based on registers (4 bytes per register)
    const registers = block.registers || [];
    const blockSize = registers.length > 0
      ? registers.length * 4
      : (typeof block.size === 'number' ? block.size : 4);

    newBlocks[i] = {
      ...block,
      base_address: nextBase,
      size: blockSize,
    };
    nextBase += blockSize;
  }

  return newBlocks;
}

/**
 * Repack address blocks backward (toward lower addresses) starting from the given index going backwards.
 * Maintains block sizes but shifts them to lower addresses.
 * Calculates block size based on number of registers (4 bytes per register).
 * @param blocks Array of address blocks
 * @param fromIndex Starting index for repacking (inclusive), goes backward to index 0
 * @returns New array with repacked blocks
 */
export function repackBlocksBackward(blocks: any[], fromIndex: number): any[] {
  const newBlocks = [...blocks];

  // Start from the block just after fromIndex to determine the starting position
  let nextEnd =
    fromIndex < newBlocks.length - 1 ? newBlocks[fromIndex + 1].base_address - 1 : Infinity;

  for (let i = fromIndex; i >= 0; i--) {
    const block = newBlocks[i];

    // Calculate size based on registers (4 bytes per register)
    const registers = block.registers || [];
    const size = registers.length > 0
      ? registers.length * 4
      : (block.size || 4);

    const base = nextEnd === Infinity ? block.base_address : nextEnd - size + 1;
    newBlocks[i] = {
      ...block,
      base_address: Math.max(0, base),
      size,
    };
    nextEnd = base - 1;
  }

  return newBlocks;
}
