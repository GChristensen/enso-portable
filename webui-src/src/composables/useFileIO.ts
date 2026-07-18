/** Read a picked file as text. */
export function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(reader.error)
    reader.readAsText(file)
  })
}

/**
 * Download text as a file.
 *
 * The old code kept a live blob URL on the toolbar anchor and refreshed it on
 * every save, which leaked a URL per keystroke-batch. Minting one per click
 * and revoking it immediately is both simpler and bounded.
 */
export function downloadText(filename: string, text: string, type = 'text/x-python') {
  const url = URL.createObjectURL(new Blob([text], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
