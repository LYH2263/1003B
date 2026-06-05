from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import date, datetime
from .models import ReadingRoom, Seat, SeatReservation


@login_required
def reading_room_manage(request):
    if request.user.role != 'admin':
        return redirect('home')
    
    rooms = ReadingRoom.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            name = request.POST.get('name')
            open_time = request.POST.get('open_time')
            close_time = request.POST.get('close_time')
            rows = int(request.POST.get('rows', 5))
            cols = int(request.POST.get('cols', 8))
            description = request.POST.get('description', '')
            
            room = ReadingRoom.objects.create(
                name=name,
                open_time=open_time,
                close_time=close_time,
                rows=rows,
                cols=cols,
                description=description
            )
            
            for row in range(1, rows + 1):
                for col in range(1, cols + 1):
                    Seat.objects.create(
                        reading_room=room,
                        seat_number=f"{row}排{col}号",
                        row=row,
                        col=col,
                        is_available=True
                    )
            
            messages.success(request, f"阅览室《{name}》创建成功！")
            return redirect('reading_room_manage')
        
        elif action == 'edit':
            room_id = request.POST.get('room_id')
            room = get_object_or_404(ReadingRoom, pk=room_id)
            
            old_rows, old_cols = room.rows, room.cols
            
            room.name = request.POST.get('name')
            room.open_time = request.POST.get('open_time')
            room.close_time = request.POST.get('close_time')
            new_rows = int(request.POST.get('rows', 5))
            new_cols = int(request.POST.get('cols', 8))
            room.description = request.POST.get('description', '')
            room.is_active = request.POST.get('is_active') == 'on'
            
            if new_rows != old_rows or new_cols != old_cols:
                Seat.objects.filter(reading_room=room).delete()
                room.rows = new_rows
                room.cols = new_cols
                
                for row in range(1, new_rows + 1):
                    for col in range(1, new_cols + 1):
                        Seat.objects.create(
                            reading_room=room,
                            seat_number=f"{row}排{col}号",
                            row=row,
                            col=col,
                            is_available=True
                        )
            
            room.save()
            messages.success(request, f"阅览室《{room.name}》更新成功！")
            return redirect('reading_room_manage')
        
        elif action == 'delete':
            room_id = request.POST.get('room_id')
            room = get_object_or_404(ReadingRoom, pk=room_id)
            room.delete()
            messages.success(request, f"阅览室《{room.name}》已删除！")
            return redirect('reading_room_manage')
    
    return render(request, 'admin/reading_room_list.html', {'rooms': rooms})


@login_required
def seat_grid_manage(request, room_id):
    if request.user.role != 'admin':
        return redirect('home')
    
    room = get_object_or_404(ReadingRoom, pk=room_id)
    seats = Seat.objects.filter(reading_room=room).order_by('row', 'col')
    
    if request.method == 'POST':
        seat_id = request.POST.get('seat_id')
        action = request.POST.get('action')
        
        if seat_id and action == 'toggle':
            seat = get_object_or_404(Seat, pk=seat_id)
            seat.is_available = not seat.is_available
            seat.save()
            return JsonResponse({
                'success': True,
                'seat_id': seat_id,
                'is_available': seat.is_available
            })
    
    seat_grid = []
    for row in range(1, room.rows + 1):
        row_seats = []
        for col in range(1, room.cols + 1):
            seat = next((s for s in seats if s.row == row and s.col == col), None)
            row_seats.append(seat)
        seat_grid.append(row_seats)
    
    return render(request, 'admin/seat_grid_manage.html', {
        'room': room,
        'seat_grid': seat_grid
    })


@login_required
def seat_reservation(request):
    rooms = ReadingRoom.objects.filter(is_active=True)
    selected_room = rooms.first()
    
    room_id = request.GET.get('room')
    if room_id:
        selected_room = get_object_or_404(ReadingRoom, pk=room_id, is_active=True)
    
    return render(request, 'seats/reservation.html', {
        'rooms': rooms,
        'selected_room': selected_room
    })


@login_required
def api_seat_status(request):
    room_id = request.GET.get('room_id')
    reservation_date = request.GET.get('date', date.today().isoformat())
    time_slot = request.GET.get('time_slot', 'morning')
    
    if not room_id:
        return JsonResponse({'error': '缺少阅览室ID'}, status=400)
    
    room = get_object_or_404(ReadingRoom, pk=room_id)
    seats = Seat.objects.filter(reading_room=room).order_by('row', 'col')
    
    reservations = SeatReservation.objects.filter(
        seat__reading_room=room,
        reservation_date=reservation_date,
        time_slot=time_slot,
        status__in=['pending', 'checked_in']
    ).select_related('seat', 'user')
    
    reserved_seat_ids = set(r.seat.id for r in reservations)
    
    seat_data = []
    for seat in seats:
        status = 'available'
        if not seat.is_available:
            status = 'unavailable'
        elif seat.id in reserved_seat_ids:
            status = 'occupied'
        
        reservation = next((r for r in reservations if r.seat.id == seat.id), None)
        
        seat_data.append({
            'id': seat.id,
            'seat_number': seat.seat_number,
            'row': seat.row,
            'col': seat.col,
            'status': status,
            'reserved_by': reservation.user.username if reservation else None
        })
    
    return JsonResponse({
        'success': True,
        'seats': seat_data,
        'rows': room.rows,
        'cols': room.cols
    })


@login_required
def api_create_reservation(request):
    if request.method != 'POST':
        return JsonResponse({'error': '方法不允许'}, status=405)
    
    seat_id = request.POST.get('seat_id')
    reservation_date = request.POST.get('date')
    time_slot = request.POST.get('time_slot')
    
    if not all([seat_id, reservation_date, time_slot]):
        return JsonResponse({'error': '缺少必要参数'}, status=400)
    
    seat = get_object_or_404(Seat, pk=seat_id)
    
    if not seat.is_available:
        return JsonResponse({'error': '该座位不可用'}, status=400)
    
    try:
        reservation = SeatReservation.objects.create(
            user=request.user,
            seat=seat,
            reservation_date=reservation_date,
            time_slot=time_slot
        )
        return JsonResponse({
            'success': True,
            'message': '预约成功！',
            'reservation_id': reservation.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def my_reservations(request):
    reservations = SeatReservation.objects.filter(user=request.user).order_by('-reservation_date', '-created_at')
    
    today = date.today()
    now = datetime.now().time()
    
    can_cancel = []
    for r in reservations:
        if r.status == 'pending' and r.reservation_date >= today:
            can_cancel.append(r.id)
    
    return render(request, 'seats/my_reservations.html', {
        'reservations': reservations,
        'can_cancel': can_cancel
    })


@login_required
def api_cancel_reservation(request, reservation_id):
    if request.method != 'POST':
        return JsonResponse({'error': '方法不允许'}, status=405)
    
    reservation = get_object_or_404(SeatReservation, pk=reservation_id, user=request.user)
    
    today = date.today()
    if reservation.reservation_date < today:
        return JsonResponse({'error': '已过期的预约不能取消'}, status=400)
    
    if reservation.status not in ['pending']:
        return JsonResponse({'error': '该状态的预约不能取消'}, status=400)
    
    reservation.status = 'cancelled'
    reservation.save()
    
    return JsonResponse({
        'success': True,
        'message': '预约已取消'
    })
