import { createSlice } from '@reduxjs/toolkit'

const roomSlice = createSlice({
  name: 'room',
  initialState: { myName: null, room: null, error: null },
  reducers: {
    setMyName(state, action) {
      state.myName = action.payload
    },
    setRoom(state, action) {
      state.room = action.payload
      state.error = null
    },
    setError(state, action) {
      state.error = action.payload
    },
    leaveRoom(state) {
      state.myName = null
      state.room = null
    },
  },
})

export const { setMyName, setRoom, setError, leaveRoom } = roomSlice.actions
export default roomSlice.reducer
