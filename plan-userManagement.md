# Plan: User-Management with Dynamic Permissions & Owner Role

**Summary**: Switch from static to dynamic permissions stored in the database, allowing role/permission management via Filament admin panel. Auto-create an "owner" role with all permissions when an organization is created. Owner becomes the sole role assigned to the organization creator initially.

## Steps

1. Design MySQL schema: add `permissions` table and `role_permission` pivot table to enable dynamic permission assignment
2. Create Eloquent models: `Permission`, and update `Role` to have many-to-many relationship with permissions
3. Seed default permissions on first migration (e.g., `users.create`, `users.edit`, `users.delete`, `organizations.manage`, `roles.manage`, etc.)
4. Create Filament resources for `Role` and `Permission` management at `/admin/roles` and `/admin/permissions`
5. Implement factory/seeder: auto-create "owner" role with all permissions when organization is created
6. Build role/permission middleware: check if user has required permission(s) for each API endpoint and admin action
7. Update user signup flow: organization creator automatically assigned "owner" role in that organization

## Further Considerations

1. **Permission scope**: Are permissions organization-level (users manage within own org) or system-level (edit any org's data)?
2. **Other roles needed**: Besides "owner," what other roles should be seeded by default (admin, manager, user, viewer, etc.), or only create dynamically?
3. **Permission granularity**: Should permissions cover actions like `users.view`, `users.create`, `users.edit`, `users.delete`, or more specific (e.g., `users.export`, `users.impersonate`)?
