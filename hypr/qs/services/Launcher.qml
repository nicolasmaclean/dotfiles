pragma Singleton

import QtQuick
import Quickshell

Singleton {
  id: root

  property bool open: false
  property string query: ""
  readonly property var apps: DesktopEntries.applications.values
  readonly property var results: getSearchResults(query)

  function toggle(): void {
    open = !open
    if (open) {
      query = ""
    }
  }

  function close(): void {
    open = false
  }

  function executeEntry(e): void {
    Quickshell.execDetached(["uwsm", "app", "--", e.id + ".desktop"])
  }

  function getSearchResults(q) {
    const visible = apps.filter(a => !a.noDisplay)
    q = q.trim().toLowerCase()

    // show all apps, if no query yet
    if (!q)
      return visible.sort((a, b) => a.name.localeCompare(b.name))

    // filter and sort based on query
    return visible.map(a => ({
          entry: a,
          score: score(a, q)
        })).filter(r => r.score > 0).sort((a, b) => b.score - a.score || a.entry.name.localeCompare(b.entry.name)).map(r => r.entry)
  }

  // higher is better, 0 means no match
  function score(app, q): int {
    const name = app.name.toLowerCase()
    if (name === q)
      return 100
    if (name.startsWith(q))
      return 80
    if (name.split(/[\s\-_.]/).some(w => w.startsWith(q)))
      return 60
    if (name.includes(q))
      return 40
    if ((app.genericName ?? "").toLowerCase().includes(q))
      return 20
    if ((app.keywords ?? []).some(k => k.toLowerCase().includes(q)))
      return 10
    return 0
  }
}
