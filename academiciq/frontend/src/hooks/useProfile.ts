import { useQuery } from '@tanstack/react-query'
import { profileApi } from '@/api/endpoints'

export function useProfile(studentId: string) {
  return useQuery({
    queryKey: ['profile', studentId],
    queryFn: () => profileApi.get(studentId).then(r => r.data),
    enabled: !!studentId,
  })
}
