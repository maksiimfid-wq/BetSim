import json
import os
from datetime import datetime
from sports_skills import football

BANK_FILE = "bankroll.json"
BETS_FILE = "active_bets.json"


def load_bankroll():
    """Loads bankroll from file"""
    if os.path.exists(BANK_FILE):
        try:
            with open(BANK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get('bankroll', 1000.0)
        except:
            return 1000.0
    return 1000.0


def save_bankroll(bankroll):
    """Saves bankroll to file"""
    with open(BANK_FILE, 'w', encoding='utf-8') as f:
        json.dump({'bankroll': bankroll}, f, indent=2)


def load_active_bets():
    """Loads active bets from file"""
    if os.path.exists(BETS_FILE):
        try:
            with open(BETS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_active_bets(bets):
    """Saves active bets to file"""
    with open(BETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(bets, f, indent=2, ensure_ascii=False)


def check_pending_bets(active_bets):
    """Checks all active bets when program starts"""
    global bankroll

    if not active_bets:
        return

    print("\n" + "=" * 60)
    print("📋 CHECKING ACTIVE BETS")
    print("=" * 60)

    updated_bets = []

    for bet in active_bets:
        ev_id = bet['event_id']

        try:
            result = football.get_event_summary(event_id=ev_id)

            if not result.get('status') or not result.get('data'):
                print(f"⚠️ Failed to check {bet['match']}")
                updated_bets.append(bet)
                continue

            result_data = result['data']['event']
            final_status = result_data['status']
            final_home = result_data['scores']['home']
            final_away = result_data['scores']['away']

            print(f"\n⚽ {bet['match']}")
            print(f"   Score: {final_home} : {final_away}")
            print(f"   Status: {final_status}")

            if final_status in ['finished', 'closed']:
                if final_home > final_away:
                    winner = 'home'
                elif final_away > final_home:
                    winner = 'away'
                else:
                    winner = 'draw'

                win = False
                if bet['choice'] == '1' and winner == 'home':
                    win = True
                elif bet['choice'] == '2' and winner == 'away':
                    win = True

                if win:
                    win_amount = bet['amount'] * bet['odds']
                    bankroll += win_amount
                    print(f"   🎉 WIN! +{win_amount - bet['amount']:.2f} u.e.")
                else:
                    print(f"   💔 LOSS! -{bet['amount']:.2f} u.e.")

            else:
                updated_bets.append(bet)
                print(f"   ⏳ Match not finished yet")

        except Exception as e:
            print(f"   ⚠️ Error: {e}")
            updated_bets.append(bet)
    save_active_bets(updated_bets)

    if updated_bets:
        print(f"\n📌 Active bets remaining: {len(updated_bets)}")

    print("=" * 60)


def show_matches():
    today = datetime.now().strftime("%Y-%m-%d")
    schedule = football.get_daily_schedule(date=today)

    if not schedule.get('status') or not schedule.get('data'):
        print("❌ Failed to get schedule")
        return

    events = schedule['data']['events']

    print("\n" + "=" * 80)
    print(f"📅 MATCHES FOR {schedule['data']['date']}")
    print("=" * 80)

    for idx, event in enumerate(events, 1):
        home = event['competitors'][0]['team']['name']
        away = event['competitors'][1]['team']['name']
        home_score = event['scores']['home']
        away_score = event['scores']['away']
        status = event['status']
        event_id = event['id']

        status_en = {
            'not_started': '⏳ Not started',
            '1st_half': '🏃 1st half',
            '2nd_half': '🏃 2nd half',
            'halftime': '⏸️ Halftime',
            'finished': '✅ Finished',
            'closed': '✅ Finished'
        }.get(status, status)

        print(f"\n{idx}. 🆔 ID: {event_id}")
        print(f"   {home} vs {away}")
        print(f"   📊 Score: {home_score} : {away_score}")
        print(f"   📌 Status: {status_en}")

        if event.get('odds') and event['odds'].get('moneyline'):
            odds_data = event['odds']['moneyline']

            def to_decimal(odds_str):
                if not odds_str or odds_str == '?':
                    return '?'
                if isinstance(odds_str, str):
                    if odds_str.startswith('-'):
                        return f"{1 + (100 / abs(int(odds_str))):.2f}"
                    elif odds_str.startswith('+'):
                        return f"{1 + (int(odds_str) / 100):.2f}"
                return odds_str

            home_odds = to_decimal(odds_data.get('home', '?'))
            draw_odds = to_decimal(odds_data.get('draw', '?'))
            away_odds = to_decimal(odds_data.get('away', '?'))

            print(f"   🎲 Odds (decimal):")
            print(f"      {home} win: {home_odds}")
            print(f"      Draw: {draw_odds}")
            print(f"      {away} win: {away_odds}")

        print("-" * 80)

    input("\n📌 Press Enter to return to menu...")


def place_bet():
    global bankroll

    ev_id = input("Enter event ID: ")

    today = datetime.now().strftime("%Y-%m-%d")
    schedule = football.get_daily_schedule(date=today)

    if not schedule.get('status') or not schedule.get('data'):
        print("❌ Failed to get schedule")
        return

    events = schedule['data']['events']
    event_data = None

    for event in events:
        if event['id'] == ev_id:
            event_data = event
            break

    if not event_data:
        print("❌ Event not found")
        return

    home_team = event_data['competitors'][0]['team']['name']
    away_team = event_data['competitors'][1]['team']['name']
    status = event_data['status']

    print(f"\n⚽ {home_team} vs {away_team}")
    print(f"📌 Status: {status}")

    if status != 'not_started':
        print("❌ Bets are only accepted before the match starts")
        return

    if not event_data.get('odds') or not event_data['odds'].get('moneyline'):
        print("❌ No odds available for this event")
        return

    odds_data = event_data['odds']['moneyline']

    print(f"\n🎲 BET OPTIONS:")
    print(f"1. {home_team} win: {odds_data.get('home', '?')}")
    print(f"2. {away_team} win: {odds_data.get('away', '?')}")

    choice = input("\nYour choice (1/2): ")

    if choice == '1':
        raw_odds = odds_data.get('home')
        selected = home_team
    else:
        raw_odds = odds_data.get('away')
        selected = away_team

    if isinstance(raw_odds, str):
        if raw_odds.startswith('-'):
            odds = 1 + (100 / abs(int(raw_odds)))
        elif raw_odds.startswith('+'):
            odds = 1 + (int(raw_odds) / 100)
        else:
            odds = float(raw_odds)
    else:
        odds = float(raw_odds)

    print(f"📊 Odds (decimal): {odds:.2f}")

    amount = float(input("💰 Bet amount: "))

    if amount > bankroll:
        print("❌ Insufficient funds")
        return

    bankroll -= amount
    print(f"\n✅ Bet accepted! {amount} u.e. deducted")
    print(f"💰 Balance: {bankroll:.2f} u.e.")

    active_bets = load_active_bets()

    new_bet = {
        'event_id': ev_id,
        'match': f"{home_team} vs {away_team}",
        'choice': choice,
        'bet_on': selected,
        'odds': odds,
        'amount': amount,
        'datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    active_bets.append(new_bet)
    save_active_bets(active_bets)
    save_bankroll(bankroll)

    print(f"\n💾 Bet saved to file! You can close the program.")

    print("\n⏳ Waiting for match to finish...")
    print("Enter 'check' to check status, 'exit' to quit")

    while True:
        command = input("\n➡️ Enter command (check/exit): ").strip().lower()

        if command == 'exit':
            print("💾 Bet saved. Check result later.")
            return

        elif command == 'check':
            # Для проверки статуса используем get_event_summary
            result = football.get_event_summary(event_id=ev_id)
            if not result.get('status') or not result.get('data'):
                print("❌ Failed to get event status")
                continue

            result_data = result['data']['event']
            final_status = result_data['status']
            final_home = result_data['scores']['home']
            final_away = result_data['scores']['away']

            print(f"\n📊 CURRENT STATUS:")
            print(f"{home_team} {final_home} : {final_away} {away_team}")
            print(f"📌 Status: {final_status}")

            if final_status in ['finished', 'closed']:
                print("\n✅ Match finished! Calculating bet...")

                if final_home > final_away:
                    winner = 'home'
                    winner_name = home_team
                elif final_away > final_home:
                    winner = 'away'
                    winner_name = away_team
                else:
                    winner = 'draw'
                    winner_name = 'Draw'

                print(f"🏆 Winner: {winner_name}")

                win = False
                if choice == '1' and winner == 'home':
                    win = True
                elif choice == '2' and winner == 'away':
                    win = True

                if win:
                    win_amount = amount * odds
                    bankroll += win_amount
                    print(f"\n🎉 YOU WIN! +{win_amount - amount:.2f} u.e.")
                else:
                    print(f"\n💔 YOU LOSE! -{amount:.2f} u.e.")

                print(f"💰 Your balance: {bankroll:.2f} u.e.")

                active_bets = load_active_bets()
                active_bets = [b for b in active_bets if b['event_id'] != ev_id]
                save_active_bets(active_bets)
                save_bankroll(bankroll)

                input("\n📌 Press Enter to return to menu...")
                break

            else:
                print("⏳ Match still in progress. Check later.")
                continue

        else:
            print("❌ Invalid command. Enter 'check' or 'exit'")


def main():
    """Main menu"""
    global bankroll

    bankroll = load_bankroll()
    active_bets = load_active_bets()

    if active_bets:
        check_pending_bets(active_bets)

    print("\n" + "=" * 50)
    print("   WELCOME TO BetSim")
    print("=" * 50)
    print(f"💰 Your current balance: {bankroll:.2f} u.e.")

    while True:
        print("\n--- MENU ---")
        print("1. 📊 View available matches")
        print("2. 🎲 Place a bet")
        print("3. 💰 Balance")
        print("4. 🚪 Exit")

        choice = input("\nSelect action (1-4): ").strip()

        if choice == '1':
            show_matches()
        elif choice == '2':
            place_bet()
        elif choice == '3':
            print(f"\n💰 Your current balance: {bankroll:.2f} u.e.")
        elif choice == '4':
            save_bankroll(bankroll)
            print("Thanks for playing! Goodbye.")
            break
        else:
            print("❌ Invalid choice. Try again.")


if __name__ == "__main__":
    main()

