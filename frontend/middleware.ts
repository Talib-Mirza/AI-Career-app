import type { NextRequest } from 'next/server'

import { updateSession } from '@/lib/supabase/middleware'

/**
 * Refreshes Supabase Auth cookies on each matched request so SSR and API routes
 * see up-to-date sessions; pairs with browser client auth from `@/lib/supabase/client`.
 */
export async function middleware(request: NextRequest) {
    return updateSession(request)
}

export const config = {
    matcher: [
        /*
         * Skip Next internals and static assets; run on everything else so auth cookies refresh on navigation.
         */
        '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
    ],
}
