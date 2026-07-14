export type NavigationRoute = {
  path: string
  hidden?: boolean
  children?: NavigationRoute[]
}

export function flattenLeafRoutes<T extends NavigationRoute>(routes: T[]): T[] {
  return routes.flatMap((route) => {
    if (route.children?.length) {
      return flattenLeafRoutes(route.children as T[])
    }

    return [route]
  })
}

export function getMenuRoutes<T extends NavigationRoute>(routes: T[]): T[] {
  return routes.filter((route) => !route.hidden)
}

export function getSelectedMenuKey(
  routes: NavigationRoute[],
  pathname: string,
  fallbackPath: string,
) {
  return (
    flattenLeafRoutes(routes).find(
      (route) => pathname === route.path || pathname.startsWith(`${route.path}/`),
    )?.path ?? fallbackPath
  )
}
