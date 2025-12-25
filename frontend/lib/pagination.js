export const getPageParam = (searchParams, paramName = 'p') => {
  const rawValue = searchParams?.get?.(paramName) || '1';
  const pageParam = Number.parseInt(rawValue, 10);
  if (Number.isNaN(pageParam) || pageParam < 1) {
    return 1;
  }
  return pageParam;
};

export const getPagination = (searchParams, perPage, paramName = 'p') => {
  const page = getPageParam(searchParams, paramName);
  const skip = (page - 1) * perPage;
  return { page, skip };
};
