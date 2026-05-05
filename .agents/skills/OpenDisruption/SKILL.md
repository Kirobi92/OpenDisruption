```markdown
# OpenDisruption Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the OpenDisruption TypeScript codebase. You'll learn about file naming, import/export styles, commit message conventions, and how to write and organize tests. This guide also provides suggested commands for common workflows to help streamline your development process.

## Coding Conventions

### File Naming
- **Pattern:** PascalCase
- **Example:**  
  ```plaintext
  UserService.ts
  EventManager.ts
  ```

### Import Style
- **Pattern:** Relative imports
- **Example:**
  ```typescript
  import { UserService } from './UserService';
  import { EventManager } from '../events/EventManager';
  ```

### Export Style
- **Pattern:** Named exports
- **Example:**
  ```typescript
  // In UserService.ts
  export function createUser() { ... }
  export const UserRole = { ... };
  ```

### Commit Message Conventions
- **Prefixes:** `feat`, `fix`
- **Average length:** ~50 characters
- **Example:**
  ```
  feat: add event dispatching to EventManager
  fix: correct user role assignment logic
  ```

## Workflows

### Feature Development
**Trigger:** When adding a new feature  
**Command:** `/feature-dev`

1. Create a new TypeScript file using PascalCase.
2. Use relative imports to include dependencies.
3. Export new functions or constants using named exports.
4. Commit changes with a `feat:` prefix and a concise message.

### Bug Fixing
**Trigger:** When fixing a bug  
**Command:** `/bug-fix`

1. Locate the relevant TypeScript file.
2. Apply the fix, following code style conventions.
3. Commit changes with a `fix:` prefix and a concise message.

### Testing
**Trigger:** When adding or updating tests  
**Command:** `/test`

1. Create or update a test file matching `*.test.ts`.
2. Place test files alongside the code or in a dedicated test directory.
3. Use the project's preferred (unknown) testing framework.
4. Run tests to ensure correctness.

## Testing Patterns

- **File Pattern:** `*.test.ts`
- **Framework:** Unknown (use standard TypeScript test frameworks like Jest or Mocha if not specified)
- **Example:**
  ```typescript
  // UserService.test.ts
  import { createUser } from './UserService';

  describe('createUser', () => {
    it('should create a user with default role', () => {
      const user = createUser('Alice');
      expect(user.role).toBe('user');
    });
  });
  ```

## Commands
| Command        | Purpose                                   |
|----------------|-------------------------------------------|
| /feature-dev   | Start a new feature development workflow   |
| /bug-fix       | Begin a bug fixing workflow               |
| /test          | Add or update tests for the codebase      |
```
