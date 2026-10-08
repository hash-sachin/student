import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { studentsApi } from '@/api/endpoints'
import type { Student } from '@/types'

export function useStudents(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: ['students', params],
    queryFn: () => studentsApi.list(params).then(r => r.data),
  })
}

export function useStudent(id: string) {
  return useQuery({
    queryKey: ['student', id],
    queryFn: () => studentsApi.get(id).then(r => r.data),
    enabled: !!id,
  })
}

export function useCreateStudent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Student>) => studentsApi.create(data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['students'] }),
  })
}
