/// <reference types="vite/client" />

// CSS Modules Type Declaration
declare module '*.module.css' {
  const classes: { [key: string]: string }
  export default classes
}

