const SLUG_STRIP = /[^\w\s-]/g

function slugify(text: string): string {
  return text.trim().toLowerCase().replace(SLUG_STRIP, '').replace(/\s+/g, '-')
}

/**
 * The id to link a heading by.
 *
 * The doc fragments came from GitHub-rendered markdown, so most headings carry
 * their id on a nested `<a class="anchor">` rather than on the heading itself.
 * A few (notably #voice-recognition, which other pages link to) have it
 * directly. Fall back to a generated slug so every entry is reachable.
 */
function headingId(heading: HTMLElement, used: Set<string>): string {
  const existing = heading.id || heading.querySelector<HTMLElement>('[id]')?.id
  if (existing) return existing

  const base = slugify(heading.textContent ?? '') || 'section'
  let id = base
  for (let n = 2; used.has(id); n++) id = `${base}-${n}`
  // Generated ids must land on the heading itself so scrolling can find them.
  heading.id = id
  return id
}

/**
 * Fill the `<ul data-toc>` placeholder in a rendered doc fragment.
 *
 * Replaces jquery.toc, which was the only reason the tutorial page loaded
 * jQuery at all.
 */
export function buildToc(root: HTMLElement): void {
  const list = root.querySelector('[data-toc]')
  if (!list) return

  // Skip headings belonging to the table of contents itself -- the "Contents"
  // label is an <h2>, and without this it lists itself as its own first entry.
  const headings = [...root.querySelectorAll<HTMLElement>('h1, h2')].filter(
    (h) => !h.closest('#toc') && !h.closest('[data-toc]'),
  )
  if (headings.length === 0) return

  const used = new Set<string>()
  list.textContent = ''
  let sublist: HTMLUListElement | null = null

  for (const heading of headings) {
    const id = headingId(heading, used)
    used.add(id)

    const item = document.createElement('li')
    const link = document.createElement('a')
    link.href = `#${id}`
    link.textContent = (heading.textContent ?? '').trim()
    item.appendChild(link)

    // An h2 nests under the preceding h1, creating the sublist on demand. With
    // no h1 before it there is nothing to nest under, so it becomes top-level
    // -- appending a <ul> straight into a <ul> would be invalid markup and is
    // what produced the stray indent.
    const parentItem = heading.tagName === 'H2' ? list.lastElementChild : null

    if (!parentItem) {
      list.appendChild(item)
      sublist = null
    } else {
      if (!sublist) {
        sublist = document.createElement('ul')
        parentItem.appendChild(sublist)
      }
      sublist.appendChild(item)
    }
  }
}
