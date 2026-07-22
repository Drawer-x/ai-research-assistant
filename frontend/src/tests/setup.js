import { vi } from 'vitest'

global.ResizeObserver = class {
  observe() {}
  disconnect() {}
}
Object.defineProperty(window, 'matchMedia', { value: vi.fn(() => ({ matches: false, addListener() {}, removeListener() {} })), writable: true })
